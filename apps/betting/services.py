from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.wallet.models import WalletAccount
from apps.wallet.services import (ensure_house_account, ensure_user_accounts, get_user_wallet_account, transfer_between_accounts,)
from apps.users.models import UserProfile
from .models import Bet, CombinedBet, CombinedBetSelection, Event, Odd

MIN_STAKE = Decimal("1.0000")
MAX_STAKE = Decimal("1000.0000")
DECIMAL_QUANTIZER = Decimal("0.0001")

def _to_decimal(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise ValidationError("Monto inválido.") from exc
    return amount.quantize(DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

def _validate_user_can_bet(user):
    profile = UserProfile.objects.filter(user=user).first()
    if not profile:
        raise ValidationError("El usuario no tiene perfil KYC.")
    if profile.kyc_status == UserProfile.KYCStatus.SELF_EXCLUDED:
        raise ValidationError("El usuario está autoexcluido.")
    if profile.kyc_status != UserProfile.KYCStatus.VERIFIED:
        raise ValidationError("El usuario debe estar verificado para apostar.")
    return profile

def place_simple_bet(user, odd: Odd, stake, idempotency_key: str) -> Bet:
    stake = _to_decimal(stake)
    if stake < MIN_STAKE or stake > MAX_STAKE:
        raise ValidationError("El monto está fuera de los límites permitidos.")
    
    if not odd.is_active:
        raise ValidationError("La cuota no está activa.")
    event = odd.event

    if event.status not in (Event.Status.PROGRAMADO, Event.Status.EN_VIVO):
        raise ValidationError("El evento no acepta apuestas en este momento.")
    
    if event.status == Event.Status.PROGRAMADO and event.start_at <= timezone.now():
        raise ValidationError("El evento ya inició.")
    
    if event.start_at <= timezone.now():
        raise ValidationError("El evento ya inició.")
    _validate_user_can_bet(user)

    existing = Bet.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing

    accounts = ensure_user_accounts(user)
    user_wallet = accounts[WalletAccount.AccountType.WALLET_USUARIO]
    pending_account = accounts[WalletAccount.AccountType.APUESTAS_PENDIENTES]

    if user_wallet.balance < stake:
        raise ValidationError("Saldo insuficiente.")

    transfer_between_accounts( from_account=user_wallet, to_account=pending_account, amount=stake, idempotency_key=idempotency_key, description="Stake para apuesta simple",)

    bet = Bet.objects.create( user=user, event=event, odd=odd, selection=odd.selection, stake=stake, odds_snapshot=odd.decimal_odds, status="accepted", idempotency_key=idempotency_key,)
    return bet


@transaction.atomic
def settle_bet(bet: Bet, result: str) -> Bet:
    bet = Bet.objects.select_for_update().get(pk=bet.pk)

    if bet.status != Bet.Status.ACCEPTED:
        return bet

    accounts = ensure_user_accounts(bet.user)
    user_wallet = accounts[WalletAccount.AccountType.WALLET_USUARIO]
    pending_account = accounts[WalletAccount.AccountType.APUESTAS_PENDIENTES]
    house_account = ensure_house_account()

    if bet.selection == result:
        payout = (bet.stake * bet.odds_snapshot).quantize(DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

        transfer_between_accounts( from_account=pending_account, to_account=house_account, amount=bet.stake, idempotency_key=f"{bet.idempotency_key}-settle-stake", description="Liquidación de apuesta ganadora: mover stake a casa",)
        transfer_between_accounts( from_account=house_account, to_account=user_wallet, amount=payout, idempotency_key=f"{bet.idempotency_key}-payout", description="Pago de apuesta ganadora",)

        bet.status = Bet.Status.WON
        bet.payout = payout
    else:
        transfer_between_accounts( from_account=pending_account, to_account=house_account, amount=bet.stake, idempotency_key=f"{bet.idempotency_key}-lost", description="Liquidación de apuesta perdida",)
        bet.status = Bet.Status.LOST
        bet.payout = Decimal("0.0000")

    bet.settled_at = timezone.now()
    bet.save(update_fields=["status", "payout", "settled_at"])
    return bet


def place_combined_bet(user, odd_ids, stake, idempotency_key: str) -> CombinedBet:
    if not odd_ids or len(odd_ids) < 2:
        raise ValidationError("La combinada debe tener al menos 2 selecciones.")

    stake = _to_decimal(stake)

    if stake < MIN_STAKE or stake > MAX_STAKE:
        raise ValidationError("El monto está fuera de los límites permitidos.")

    _validate_user_can_bet(user)

    existing = CombinedBet.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing

    odd_ids_unique = list(dict.fromkeys(odd_ids))
    odds_qs = (
        Odd.objects.select_related("event")
        .filter(id__in=odd_ids_unique, is_active=True)
    )
    odds_map = {odd.id: odd for odd in odds_qs}

    if len(odds_map) != len(odd_ids_unique):
        raise ValidationError("Una o más cuotas no existen o están inactivas.")

    odds = [odds_map[odd_id] for odd_id in odd_ids_unique]

    events_seen = set()
    combined_odds = Decimal("1.0000")

    for odd in odds:
        if odd.event_id in events_seen:
            raise ValidationError("No se puede combinar más de una selección del mismo partido.")
        events_seen.add(odd.event_id)

        if odd.event.status != Event.Status.PROGRAMADO:
            raise ValidationError("Todos los eventos de una combinada deben estar programados.")

        if odd.event.start_at <= timezone.now():
            raise ValidationError("No se puede apostar a un evento ya iniciado.")

        combined_odds *= odd.decimal_odds

    combined_odds = combined_odds.quantize(DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

    accounts = ensure_user_accounts(user)
    user_wallet = accounts[WalletAccount.AccountType.WALLET_USUARIO]
    pending_account = accounts[WalletAccount.AccountType.APUESTAS_PENDIENTES]

    if user_wallet.balance < stake:
        raise ValidationError("Saldo insuficiente.")

    transfer_between_accounts( from_account=user_wallet, to_account=pending_account, amount=stake, idempotency_key=idempotency_key, description="Stake para apuesta combinada", )

    combined_bet = CombinedBet.objects.create( user=user, stake=stake, odds_snapshot=combined_odds, selection_count=len(odds), status="accepted", idempotency_key=idempotency_key,)

    for odd in odds:
        CombinedBetSelection.objects.create( combined_bet=combined_bet, event=odd.event, odd=odd, selection=odd.selection, odds_snapshot=odd.decimal_odds,)
    return combined_bet


@transaction.atomic
def settle_combined_bet(combined_bet: CombinedBet) -> CombinedBet:
    combined_bet = CombinedBet.objects.select_for_update().get(pk=combined_bet.pk)

    if combined_bet.status != CombinedBet.Status.ACCEPTED:
        return combined_bet

    selections = list(
        combined_bet.selections.select_related("event", "odd").order_by("id")
    )

    if not selections:
        raise ValidationError("La combinada no tiene selecciones.")

    for selection in selections:
        if selection.event.result is None:
            raise ValidationError("No se puede liquidar una combinada con eventos sin resultado.")

    all_won = all(selection.selection == selection.event.result for selection in selections)

    accounts = ensure_user_accounts(combined_bet.user)
    user_wallet = accounts[WalletAccount.AccountType.WALLET_USUARIO]
    pending_account = accounts[WalletAccount.AccountType.APUESTAS_PENDIENTES]
    house_account = ensure_house_account()

    if all_won:
        payout = (
            combined_bet.stake * combined_bet.odds_snapshot
        ).quantize(DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

        transfer_between_accounts( from_account=pending_account, to_account=house_account, amount=combined_bet.stake, idempotency_key=f"{combined_bet.idempotency_key}-stake", description="Liquidación de combinada ganadora: mover stake a casa",)
        transfer_between_accounts( from_account=house_account, to_account=user_wallet, amount=payout, idempotency_key=f"{combined_bet.idempotency_key}-payout", description="Pago de combinada ganadora",)

        combined_bet.status = CombinedBet.Status.WON
        combined_bet.payout = payout
    else:
        transfer_between_accounts(from_account=pending_account, to_account=house_account, amount=combined_bet.stake, idempotency_key=f"{combined_bet.idempotency_key}-lost", description="Liquidación de combinada perdida",)

        combined_bet.status = CombinedBet.Status.LOST
        combined_bet.payout = Decimal("0.0000")

    combined_bet.settled_at = timezone.now()
    combined_bet.save(update_fields=["status", "payout", "settled_at"])
    return combined_bet


@transaction.atomic
def settle_event(event: Event, result: str) -> Event:
    event = Event.objects.select_for_update().get(pk=event.pk)

    if event.status == Event.Status.FINALIZADO:
        raise ValidationError("El evento ya fue liquidado.")

    event.status = Event.Status.FINALIZADO
    event.result = result
    event.save(update_fields=["status", "result", "updated_at"])

    bets = Bet.objects.select_for_update().filter(event=event, status=Bet.Status.ACCEPTED)
    for bet in bets:
        settle_bet(bet, result)

    combined_bets = (
        CombinedBet.objects.select_for_update()
        .filter(selections__event=event, status=CombinedBet.Status.ACCEPTED)
        .distinct()
    )

    for combined_bet in combined_bets:
        selections = combined_bet.selections.select_related("event", "odd").all()
        if all(selection.event.result is not None for selection in selections):
            settle_combined_bet(combined_bet)

    return event

def calculate_cashout_amount(bet: Bet, factor_house: Decimal = Decimal("0.95")) -> Decimal:
    current_odds = bet.odd.decimal_odds
    if current_odds <= 0:
        raise ValidationError("La cuota actual no es válida.")

    cashout = (bet.stake * bet.odds_snapshot / current_odds) * factor_house
    return cashout.quantize(DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


@transaction.atomic
def cash_out_bet(bet: Bet) -> Bet:
    bet = Bet.objects.select_for_update().select_related("odd", "event", "user").get(pk=bet.pk)

    if bet.status != Bet.Status.ACCEPTED:
        raise ValidationError("Solo se puede hacer cash-out en apuestas aceptadas.")

    if bet.event.status == Event.Status.FINALIZADO:
        raise ValidationError("No se puede hacer cash-out en un evento finalizado.")

    accounts = ensure_user_accounts(bet.user)
    user_wallet = accounts[WalletAccount.AccountType.WALLET_USUARIO]
    pending_account = accounts[WalletAccount.AccountType.APUESTAS_PENDIENTES]
    house_account = ensure_house_account()

    cashout_amount = calculate_cashout_amount(bet)

    transfer_between_accounts(
        from_account=pending_account,
        to_account=house_account,
        amount=bet.stake,
        idempotency_key=f"{bet.idempotency_key}-cashout-stake",
        description="Cash-out: mover stake a casa",
    )

    transfer_between_accounts(
        from_account=house_account,
        to_account=user_wallet,
        amount=cashout_amount,
        idempotency_key=f"{bet.idempotency_key}-cashout-payout",
        description="Cash-out: pago anticipado",
    )

    bet.status = Bet.Status.CASHED_OUT
    bet.payout = cashout_amount
    bet.settled_at = timezone.now()
    bet.save(update_fields=["status", "payout", "settled_at"])
    return bet