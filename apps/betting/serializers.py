from decimal import Decimal

from rest_framework import serializers

from .models import Bet, Event, Odd


class OddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Odd
        fields = ("id", "selection", "decimal_odds", "is_active")


class EventSerializer(serializers.ModelSerializer):
    odds = OddSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "home_team",
            "away_team",
            "start_at",
            "status",
            "result",
            "odds",
            "created_at",
        )


class BetSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    odd_id = serializers.IntegerField(source="odd.id", read_only=True)

    class Meta:
        model = Bet
        fields = (
            "id",
            "transaction_id",
            "idempotency_key",
            "event",
            "odd_id",
            "selection",
            "stake",
            "odds_snapshot",
            "status",
            "payout",
            "placed_at",
            "settled_at",
        )


class PlaceBetSerializer(serializers.Serializer):
    odd_id = serializers.IntegerField()
    stake = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("1.0000"))
    idempotency_key = serializers.CharField(max_length=120)

    def validate_odd_id(self, value):
        try:
            return Odd.objects.get(pk=value)
        except Odd.DoesNotExist as exc:
            raise serializers.ValidationError("La cuota no existe.") from exc


class SettleEventSerializer(serializers.Serializer):
    result = serializers.ChoiceField(choices=Event.Result.choices)