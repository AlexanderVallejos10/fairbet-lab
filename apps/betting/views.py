from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import (
    cash_out_bet,
    place_combined_bet,
    place_simple_bet,
    settle_event,
)
from .models import Bet, CombinedBet, Event
from .serializers import (
    BetSerializer,
    CombinedBetSerializer,
    EventSerializer,
    PlaceBetSerializer,
    PlaceCombinedBetSerializer,
    SettleEventSerializer,
)
from .services import place_combined_bet, place_simple_bet, settle_event


class EventListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        events = Event.objects.prefetch_related("odds").order_by("start_at")
        return Response(EventSerializer(events, many=True).data)


class BetListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bets = (
            Bet.objects.filter(user=request.user)
            .select_related("event", "odd")
            .prefetch_related("event__odds")
            .order_by("-placed_at")
        )
        return Response(BetSerializer(bets, many=True).data)


class CombinedBetListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bets = (
            CombinedBet.objects.filter(user=request.user)
            .prefetch_related("selections__event", "selections__odd")
            .order_by("-placed_at")
        )
        return Response(CombinedBetSerializer(bets, many=True).data)


class PlaceBetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PlaceBetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        odd = serializer.validated_data["odd_id"]
        bet = place_simple_bet(
            user=request.user,
            odd=odd,
            stake=serializer.validated_data["stake"],
            idempotency_key=serializer.validated_data["idempotency_key"],
        )

        return Response(
            {
                "message": "Apuesta creada correctamente.",
                "bet": BetSerializer(bet).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PlaceCombinedBetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PlaceCombinedBetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        combined_bet = place_combined_bet(
            user=request.user,
            odd_ids=serializer.validated_data["odd_ids"],
            stake=serializer.validated_data["stake"],
            idempotency_key=serializer.validated_data["idempotency_key"],
        )

        return Response(
            {
                "message": "Combinada creada correctamente.",
                "combined_bet": CombinedBetSerializer(combined_bet).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SettleEventView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, event_id):
        serializer = SettleEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = Event.objects.get(pk=event_id)
        event = settle_event(event, serializer.validated_data["result"])

        return Response(
            {
                "message": "Evento liquidado correctamente.",
                "event": EventSerializer(event).data,
            }
        )
    

class CashOutBetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, bet_id):
        bet = Bet.objects.select_related("event", "odd", "user").get(pk=bet_id, user=request.user)
        bet = cash_out_bet(bet)

        return Response(
            {
                "message": "Cash-out realizado correctamente.",
                "bet": BetSerializer(bet).data,
            },
            status=status.HTTP_200_OK,
        )