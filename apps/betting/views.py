from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Bet, Event
from .serializers import (
    BetSerializer,
    EventSerializer,
    PlaceBetSerializer,
    SettleEventSerializer,
)
from .services import place_simple_bet, settle_event


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