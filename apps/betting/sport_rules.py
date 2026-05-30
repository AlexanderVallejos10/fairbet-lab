from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from apps.betting.choices import BetStatus
from apps.betting.models import AccumulatedBetLeg, Bet, Event, Market

SPORT_ALLOWED_MARKETS = {
    Event.Sport.FUTBOL: {Market.Type.UNO_X_DOS,Market.Type.OVER_UNDER,Market.Type.BTTS,},
    Event.Sport.BASQUET: {Market.Type.WINNER,Market.Type.HANDICAP,Market.Type.TOTALS,},
    Event.Sport.VOLEY: {Market.Type.WINNER,Market.Type.SETS,Market.Type.TOTALS,},}

def allowed_markets_for_sport(sport: str) -> set[str]:
    return SPORT_ALLOWED_MARKETS.get(sport, set())

def _sum_stake(qs):
    total = qs.aggregate(total=Sum('stake'))['total']
    return total or Decimal('0.0000')

def current_market_bet_count(market: Market) -> int:
    simple_bets = Bet.objects.filter(
        market=market,
        status=BetStatus.ACCEPTED,
    ).count()

    accumulator_bets = AccumulatedBetLeg.objects.filter(
        market=market,
        accumulated_bet__status=BetStatus.ACCEPTED,
    ).values('accumulated_bet_id').distinct().count()
    return simple_bets + accumulator_bets

def current_market_exposure(market: Market) -> Decimal:
    return _sum_stake(
        Bet.objects.filter(market=market,status=BetStatus.ACCEPTED,))

def current_event_exposure(event: Event) -> Decimal:
    return _sum_stake(
        Bet.objects.filter( market__event=event,status=BetStatus.ACCEPTED,) )

def reopen_market_if_due(market: Market) -> Market:
    
    now = timezone.now()
    if (
        market.status == Market.Status.SUSPENDIDO
        and market.suspended_until
        and now >= market.suspended_until
    ):
        market.status = Market.Status.ABIERTO
        market.suspended_until = None
        market.save(update_fields=['status', 'suspended_until'])
    return market

def normalize_sport(value: str) -> str:
    return (value or '').strip().lower()

def sport_allows_live_betting(event: Event) -> bool:
    return event.live_betting_enabled and normalize_sport(event.sport) in {
        Event.Sport.FUTBOL,Event.Sport.BASQUET,Event.Sport.VOLEY,}

def can_bet_on_selection(selection, stake=None):
    market = selection.market
    event = market.event
    now = timezone.now()
    market = reopen_market_if_due(market)
    if event.sport not in SPORT_ALLOWED_MARKETS:
        return False, f'El deporte "{event.get_sport_display()}" no está habilitado.'

    if market.market_type not in SPORT_ALLOWED_MARKETS[event.sport]:
        return (False,f'El mercado "{market.name}" no está permitido para {event.get_sport_display()}.',)

    if event.status == Event.Status.SUSPENDIDO:
        return False, f'El evento "{event.name}" está suspendido.'

    if event.status in (Event.Status.FINALIZADO, Event.Status.ANULADO):
        return False, f'El evento "{event.name}" ya no está disponible para apuestas.'

    if market.suspended_until and timezone.now() < market.suspended_until:
        return (False,f'El mercado "{market.name}" está bloqueado temporalmente hasta {market.suspended_until}.',)

    if market.status != Market.Status.ABIERTO:
        return False, f'El mercado "{market.name}" no está abierto.'

    started = now >= event.starts_at
    if started and not sport_allows_live_betting(event):
        return False, 'Las apuestas se bloquearon al iniciar el evento para este deporte.'

    if stake is not None:
        stake = Decimal(str(stake))

        if market.max_bets is not None and current_market_bet_count(market) >= market.max_bets:
            return False, f'El mercado "{market.name}" alcanzó su máximo de apuestas.'

        if market.max_exposure is not None:
            if current_market_exposure(market) + stake > market.max_exposure:
                return False, f'El mercado "{market.name}" alcanzó su exposición máxima.'

        if event.max_event_exposure is not None:
            if current_event_exposure(event) + stake > event.max_event_exposure:
                return False, f'El evento "{event.name}" alcanzó su exposición máxima.'

    if event.max_bets is not None:
        total_open = current_event_exposure(event)
        if total_open and event.max_bets and int(total_open) >= int(event.max_bets):
            return False, f'El evento "{event.name}" alcanzó su límite máximo de apuestas.'

    return True, 'OK'