import uuid
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from apps.betting.choices import BetStatus
from apps.betting.models import AccumulatedBet, AccumulatedBetLeg, Bet, Event, Market
from apps.betting.sport_rules import can_bet_on_selection
from apps.users.choices import AccountStatus
from apps.wallet.models import AccountType, Direction, LedgerEntry
from apps.wallet.services import (_calcular_saldo,_crear_par_balanceado, _get_account,_get_global_account, _lock_account,reserve_for_bet,settle_loss,settle_win,)

class CashoutNoPermitido(Exception):
    pass

def _cashout_entry(transaction_id):
    return (
        LedgerEntry.objects.filter(
            transaction_id=transaction_id,
            direction=Direction.CREDIT,
            account__type=AccountType.WALLET_USUARIO,
        )
        .select_related('account')
        .first()
    )


def cashout(bet, odds_actual, transaction_id=None):
    if odds_actual <= Decimal('0'):
        raise ValueError('odds_actual debe ser mayor a cero.')

    if transaction_id:
        existing_entry = _cashout_entry(transaction_id)
        if existing_entry:
            return existing_entry.amount, _calcular_saldo(existing_entry.account)

    with transaction.atomic():
        bet = (
            Bet.objects.select_for_update()
            .select_related('market', 'user')
            .get(pk=bet.pk)
        )

        if transaction_id:
            existing_entry = _cashout_entry(transaction_id)
            if existing_entry:
                return existing_entry.amount, _calcular_saldo(existing_entry.account)

        if bet.status != BetStatus.ACCEPTED:
            raise CashoutNoPermitido('Solo se permite cashout de apuestas accepted.')
        if bet.market.status != Market.Status.ABIERTO:
            raise CashoutNoPermitido('El mercado no esta abierto.')
        if bet.is_settled:
            raise CashoutNoPermitido('No se puede hacer cashout de una apuesta liquidada o cancelada.')

        cashout_value = (
            bet.stake * bet.odds / odds_actual * Decimal('0.85')
        ).quantize(Decimal('0.0001'))

        wallet = _get_account(bet.user, AccountType.WALLET_USUARIO)
        wallet = _lock_account(wallet)
        pendientes = _get_global_account(AccountType.APUESTAS_PENDIENTES)

        _crear_par_balanceado(
            cuenta_origen=pendientes,
            cuenta_destino=wallet,
            amount=cashout_value,
            description='cashout de apuesta',
            transaction_id=transaction_id,
        )

        bet.status = BetStatus.CANCELLED
        bet.save(update_fields=['status'])
        return cashout_value, _calcular_saldo(wallet)


def place_accumulator(user, selections_data, stake, transaction_id=None):
    if user.account_status != AccountStatus.VERIFICADO:
        raise ValueError('Tu cuenta debe estar verificada para apostar.')

    if len(selections_data) < 2:
        raise ValueError('La combinada debe tener al menos 2 selecciones.')

    seen_markets = set()
    combined_odds = Decimal('1.0000')
    legs_info = []

    for sel_data in selections_data:
        selection = sel_data['selection']
        market = selection.market

        if market.id in seen_markets:
            raise ValueError(f'Dos selecciones del mismo mercado ({market.name}) no son válidas.')
        seen_markets.add(market.id)

        allowed, message = can_bet_on_selection(selection, stake=stake)
        if not allowed:
            raise ValueError(message)

        combined_odds = (combined_odds * selection.odds).quantize(Decimal('0.0001'))
        legs_info.append({'selection': selection, 'market': market, 'odds': selection.odds})

    existing = AccumulatedBet.objects.filter(transaction_id=transaction_id, user=user).first()
    if existing:
        return existing

    with transaction.atomic():
        reserve_for_bet(user, stake, transaction_id=transaction_id)

        acc = AccumulatedBet.objects.create(
            user=user,
            stake=stake,
            combined_odds=combined_odds,
            transaction_id=transaction_id,
        )

        for leg in legs_info:
            AccumulatedBetLeg.objects.create(
                accumulated_bet=acc,
                selection=leg['selection'],
                market=leg['market'],
                odds_at_bet=leg['odds'],
            )

    return acc


def settle_accumulator_legs(event, winning_selection_name):

    market_ids = list(event.markets.values_list('id', flat=True))
    affected_accumulator_ids = (
        AccumulatedBetLeg.objects
        .filter(market_id__in=market_ids)
        .values_list('accumulated_bet_id', flat=True)
        .distinct()
    )

    for acc_id in affected_accumulator_ids:
        with transaction.atomic():
            acc = (
                AccumulatedBet.objects
                .select_for_update()
                .select_related('user')
                .prefetch_related('legs')
                .get(pk=acc_id)
            )

            if acc.status != BetStatus.ACCEPTED:
                continue

            for leg in acc.legs.all():
                if leg.market_id in market_ids and not leg.settled:
                    leg.settled = True
                    leg.won = (leg.selection.name == winning_selection_name)
                    leg.save(update_fields=['settled', 'won'])

            all_legs = list(acc.legs.all())
            any_lost = any(leg.settled and leg.won is False for leg in all_legs)
            all_settled_and_won = all(leg.settled and leg.won is True for leg in all_legs)

            settlement_tid = uuid.uuid5(uuid.NAMESPACE_URL, f'acc-settlement:{acc.transaction_id}')

            if any_lost:
                settle_loss(acc.user, acc.stake, transaction_id=settlement_tid)
                acc.status = BetStatus.SETTLED_LOST

                for leg in all_legs:
                    if not leg.settled:
                        leg.settled = True
                        leg.won = False
                        leg.save(update_fields=['settled', 'won'])

                acc.save(update_fields=['status'])
                continue

            if all_settled_and_won:
                settle_win(acc.user, acc.stake, acc.combined_odds, transaction_id=settlement_tid)
                acc.status = BetStatus.SETTLED_WON
                acc.save(update_fields=['status'])


def settle_event(event, winning_selection_name):
    
    settled_won = 0
    settled_lost = 0

    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event.pk)

        bets = (
            Bet.objects.select_for_update()
            .select_related('selection', 'user')
            .filter(market__event=event, status=BetStatus.ACCEPTED)
        )

        for bet in bets:
            settlement_tid = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f'bet-settlement:{bet.transaction_id}',
            )
            if bet.selection.name == winning_selection_name:
                settle_win(bet.user, bet.stake, bet.odds, transaction_id=settlement_tid)
                bet.status = BetStatus.SETTLED_WON
                settled_won += 1
            else:
                settle_loss(bet.user, bet.stake, transaction_id=settlement_tid)
                bet.status = BetStatus.SETTLED_LOST
                settled_lost += 1
            bet.save(update_fields=['status'])

        Market.objects.filter(event=event).update(status=Market.Status.LIQUIDADO)
        event.status = Event.Status.FINALIZADO
        event.save(update_fields=['status'])

        settle_accumulator_legs(event, winning_selection_name)

    return settled_won, settled_lost