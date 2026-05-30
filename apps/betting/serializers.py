from decimal import Decimal
from rest_framework import serializers
from .models import Bet, CombinedBet, CombinedBetSelection, Event, Odd

class OddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Odd
        fields = ("id", "selection", "decimal_odds", "is_active", "updated_at")
class EventSerializer(serializers.ModelSerializer):
    odds = OddSerializer(many=True, read_only=True)
    class Meta:
        model = Event
        fields = ( "id", "sport", "home_team", "away_team", "start_at", "status", "result", "max_total_bets", "max_bets_per_user", "max_event_exposure", "odds", "created_at",)
class BetSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    odd_id = serializers.IntegerField(source="odd.id", read_only=True)
    ticket_code = serializers.CharField(read_only=True)
    class Meta:
        model = Bet
        fields = ("id", "ticket_code", "transaction_id", "idempotency_key", "event", "odd_id", "selection","stake", "odds_snapshot", "status", "payout", "placed_at", "settled_at",)
class CombinedBetSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CombinedBetSelection
        fields = ("id", "event", "selection", "odds_snapshot")
class CombinedBetSerializer(serializers.ModelSerializer):
    selections = CombinedBetSelectionSerializer(many=True, read_only=True)
    class Meta:
        model = CombinedBet
        fields = ("id", "transaction_id", "idempotency_key", "stake", "odds_snapshot", "selection_count", "status", "payout", "placed_at", "settled_at", "selections",)
        read_only_fields = fields

class PlaceBetSerializer(serializers.Serializer):
    odd_id = serializers.IntegerField()
    stake = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("1.0000"))
    idempotency_key = serializers.CharField(max_length=120)

    def validate_odd_id(self, value):
        try:
            return Odd.objects.get(pk=value)
        except Odd.DoesNotExist as exc:
            raise serializers.ValidationError("La cuota no existe.") from exc

class PlaceCombinedBetSerializer(serializers.Serializer):
    odd_ids = serializers.ListField( child=serializers.IntegerField(min_value=1), min_length=2,)
    stake = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("1.0000"))
    idempotency_key = serializers.CharField(max_length=120)

    def validate_odd_ids(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("No repitas la misma cuota en la combinada.")
        return value

class SettleEventSerializer(serializers.Serializer):
    result = serializers.ChoiceField(choices=Event.Result.choices)

class CashOutSerializer(serializers.Serializer):
    pass
