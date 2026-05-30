import uuid
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.betting.choices import BetStatus
from apps.betting.models import AccumulatedBet, Bet, Event, Market, Selection
from apps.betting.serializers import (AccumulatedBetCreateSerializer,AccumulatedBetSerializer,BetCreateSerializer,BetSerializer,CashoutSerializer,EventSettleSerializer,)
from apps.betting.sport_rules import can_bet_on_selection, reopen_market_if_due
from apps.betting.services import ( CashoutNoPermitido,cashout,place_accumulator,settle_event,)
from apps.users.choices import AccountStatus
from apps.wallet.services import (SaldoInsuficiente,reserve_for_bet,)

RESPONSIBLE_GAMBLING_MESSAGE = ('Juega con responsabilidad. Si crees que tienes un problema, usa la opción de autoexclusión.')
PLATFORM_NOTICE = 'Plataforma educativa con moneda virtual. No constituye una casa de apuestas.'

def _bet_response_data(bet):
    data = BetSerializer(bet).data
    data['responsible_gambling_message'] = RESPONSIBLE_GAMBLING_MESSAGE
    data['platform_notice'] = PLATFORM_NOTICE
    return data

def _get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def _reactivate_market_if_expired(market):
    return reopen_market_if_due(market)

class BetCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.account_status != AccountStatus.VERIFICADO:
            return Response(
                {'detail': 'Tu cuenta debe estar verificada y habilitada para apostar.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        selection_id = request.data.get('selection')
        if selection_id:
            candidate = (
                Selection.objects
                .select_related('market__event')
                .filter(pk=selection_id)
                .first()
            )
            if candidate:
                _reactivate_market_if_expired(candidate.market)

        serializer = BetCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        idempotency_key = request.headers.get('Idempotency-Key')
        try:
            transaction_id = uuid.UUID(idempotency_key) if idempotency_key else uuid.uuid4()
        except ValueError:
            return Response(
                {'detail': 'Idempotency-Key debe ser un UUID valido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_bet = Bet.objects.filter(transaction_id=transaction_id, user=request.user).first()
        if existing_bet:
            return Response(_bet_response_data(existing_bet), status=status.HTTP_200_OK)

        selection = serializer.validated_data['selection']
        stake = serializer.validated_data['stake']
        odds_expected = serializer.validated_data.get('odds_expected')

        try:
            with transaction.atomic():
                selection = (
                    Selection.objects
                    .select_for_update()
                    .select_related('market__event')
                    .get(pk=selection.pk)
                )

                _reactivate_market_if_expired(selection.market)

                allowed, message = can_bet_on_selection(selection, stake=stake)
                if not allowed:
                    return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)

                if odds_expected is not None and selection.odds != odds_expected:
                    return Response(
                        {
                            'detail': 'Las cuotas han cambiado. Por favor, confirme con las nuevas cuotas.',
                            'odds_expected': str(odds_expected),
                            'odds_current': str(selection.odds),
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                reserve_for_bet(request.user, stake, transaction_id=transaction_id)

                bet = Bet.objects.create(
                    user=request.user,
                    market=selection.market,
                    selection=selection,
                    stake=stake,
                    odds=selection.odds,
                    ip_address=_get_client_ip(request),
                    transaction_id=transaction_id,
                )
        except SaldoInsuficiente as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(_bet_response_data(bet), status=status.HTTP_201_CREATED)

class BetCashoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = CashoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bet = get_object_or_404(Bet.objects.select_related('user', 'market'), pk=pk)
        if bet.user_id != request.user.id:
            return Response(
                {'detail': 'La apuesta no pertenece al usuario autenticado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        idempotency_key = request.headers.get('Idempotency-Key')
        try:
            transaction_id = uuid.UUID(idempotency_key) if idempotency_key else uuid.uuid4()
        except ValueError:
            return Response(
                {'detail': 'Idempotency-Key debe ser un UUID valido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cashout_value, balance = cashout(
                bet,
                serializer.validated_data['odds_actual'],
                transaction_id=transaction_id,
            )
        except (CashoutNoPermitido, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        bet.refresh_from_db()
        return Response(
            {
                'bet_id': bet.id,
                'cashout_value': str(cashout_value),
                'balance': str(balance),
                'status': bet.status,
            },
            status=status.HTTP_200_OK,
        )

class EventSettleView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        serializer = EventSettleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        winning_selection_name = serializer.winning_selection_name
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Evento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            settled_won, settled_lost = settle_event(event, winning_selection_name)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'event': event.id,
                'result': winning_selection_name,
                'settled_won': settled_won,
                'settled_lost': settled_lost,
            },
            status=status.HTTP_200_OK,
        )

class AccumulatedBetCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.account_status != AccountStatus.VERIFICADO:
            return Response(
                {'detail': 'Tu cuenta debe estar verificada para apostar.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        selection_ids = request.data.get('selections') or []
        if isinstance(selection_ids, list):
            for selection_id in selection_ids:
                candidate = (
                    Selection.objects
                    .select_related('market__event')
                    .filter(pk=selection_id)
                    .first()
                )
                if candidate:
                    _reactivate_market_if_expired(candidate.market)

        serializer = AccumulatedBetCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        idempotency_key = request.headers.get('Idempotency-Key')
        try:
            transaction_id = uuid.UUID(idempotency_key) if idempotency_key else uuid.uuid4()
        except ValueError:
            return Response(
                {'detail': 'Idempotency-Key debe ser un UUID valido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            acc = place_accumulator(
                request.user,
                [{'selection': s} for s in serializer.validated_data['selections']],
                serializer.validated_data['stake'],
                transaction_id=transaction_id,
            )
        except (SaldoInsuficiente, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AccumulatedBetSerializer(acc).data, status=status.HTTP_201_CREATED)


class AccumulatedBetListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accumulators = (
            AccumulatedBet.objects
            .filter(user=request.user)
            .prefetch_related('legs__selection', 'legs__market__event')
            .order_by('-created_at')
        )
        return Response(AccumulatedBetSerializer(accumulators, many=True).data)


class SuspendMarketView(APIView):

    permission_classes = [IsAdminUser]

    def post(self, request, event_id):
        market_id = request.data.get('market_id')
        duration = request.data.get('duration_minutes', request.data.get('duration_seconds', 30))

        if not market_id:
            return Response(
                {'detail': 'market_id es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'detail': 'duration_minutes debe ser un entero positivo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                market = (
                    Market.objects
                    .select_for_update()
                    .get(pk=market_id, event_id=event_id)
                )
                if market.status not in (Market.Status.ABIERTO, Market.Status.SUSPENDIDO):
                    return Response(
                        {'detail': f'No se puede suspender un mercado en estado "{market.status}".'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                market.status = Market.Status.SUSPENDIDO
                market.suspended_until = timezone.now() + timedelta(minutes=duration)
                market.save(update_fields=['status', 'suspended_until'])
        except Market.DoesNotExist:
            return Response(
                {'detail': 'Mercado no encontrado para este evento.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                'market_id': market_id,
                'status': Market.Status.SUSPENDIDO,
                'suspended_until': market.suspended_until.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class EventOddsView(APIView):
    
    permission_classes = []

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        selections_data = {}

        for market in event.markets.all().prefetch_related('selections'):
            _reactivate_market_if_expired(market)
            selections_data[market.id] = {
                'market_name': market.name,
                'selections': list(market.selections.values('id', 'name', 'odds')),
                'status': market.status,
                'suspended_until': market.suspended_until.isoformat() if market.suspended_until else None,
            }

        return Response(
            {
                'event_id': event.id,
                'event_name': event.name,
                'status': event.status,
                'starts_at': event.starts_at.isoformat(),
                'markets': selections_data,
                'timestamp': timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )