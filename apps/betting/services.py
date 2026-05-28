from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.users.models import UserProfile
from apps.wallet.models import WalletAccount
from apps.wallet.services import (
    ensure_house_account,
    ensure_user_accounts,
    get_user_wallet_account,
    transfer_between_accounts,
)

from .models import Bet, Event, Odd

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

    if event.status != Event.Status.PROGRAMADO:
        raise ValidationError("El evento ya no acepta apuestas prepartido.")

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

    transfer_between_accounts(
        from_account=user_wallet,
        to_account=pending_account,
        amount=stake,
        idempotency_key=idempotency_key,
        description="Stake para apuesta simple",
    )

    bet = Bet.objects.create(
        user=user,
        event=event,
        odd=odd,
        selection=odd.selection,
        stake=stake,
        odds_snapshot=odd.decimal_odds,
        status=Bet.Status.ACCEPTED,
        idempotency_key=idempotency_key,
    )

    return bet


def settle_bet(bet: Bet, result: str) -> Bet:
    if bet.status != Bet.Status.ACCEPTED:
        return bet

    accounts = ensure_user_accounts(bet.user)
    user_wallet = accounts[WalletAccount.AccountType.WALLET_USUARIO]
    pending_account = accounts[WalletAccount.AccountType.APUESTAS_PENDIENTES]
    house_account = ensure_house_account()

    if bet.selection == result:
        payout = (bet.stake * bet.odds_snapshot).quantize(DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

        transfer_between_accounts(
            from_account=pending_account,
            to_account=house_account,
            amount=bet.stake,
            idempotency_key=f"{bet.idempotency_key}-settle-stake",
            description="Liquidación de apuesta ganadora: mover stake a casa",
        )

        transfer_between_accounts(
            from_account=house_account,
            to_account=user_wallet,
            amount=payout,
            idempotency_key=f"{bet.idempotency_key}-payout",
            description="Pago de apuesta ganadora",
        )

        bet.status = Bet.Status.WON
        bet.payout = payout
    else:
        transfer_between_accounts(
            from_account=pending_account,
            to_account=house_account,
            amount=bet.stake,
            idempotency_key=f"{bet.idempotency_key}-lost",
            description="Liquidación de apuesta perdida",
        )

        bet.status = Bet.Status.LOST
        bet.payout = Decimal("0.0000")

    bet.settled_at = timezone.now()
    bet.save(update_fields=["status", "payout", "settled_at"])
    return bet


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

    return event