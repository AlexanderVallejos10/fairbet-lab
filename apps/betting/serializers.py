from decimal import Decimal

from django.conf import settings
from rest_framework import serializers

from apps.betting.models import AccumulatedBet, AccumulatedBetLeg, Bet, Event, Market, Selection
from apps.betting.sport_rules import can_bet_on_selection
from apps.users.choices import AccountStatus


class AccumulatedBetLegSerializer(serializers.ModelSerializer):
    selection_name = serializers.CharField(source='selection.name', read_only=True)
    event_name = serializers.CharField(source='market.event.name', read_only=True)

    class Meta:
        model = AccumulatedBetLeg
        fields = [
            'id',
            'selection',
            'selection_name',
            'market',
            'event_name',
            'odds_at_bet',
            'settled',
            'won',
        ]


class AccumulatedBetSerializer(serializers.ModelSerializer):
    legs = AccumulatedBetLegSerializer(many=True, read_only=True)
    combined_odds = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    transaction_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = AccumulatedBet
        fields = [
            'id',
            'stake',
            'combined_odds',
            'status',
            'transaction_id',
            'created_at',
            'legs',
        ]


class AccumulatedBetCreateSerializer(serializers.Serializer):
    selections = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Selection.objects.select_related('market__event')
        ),
        min_length=2,
    )
    stake = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        min_value=Decimal('0.0001'),
    )

    def validate_selections(self, selections):
        seen_markets = {}
        for sel in selections:
            market = sel.market
            if market.id in seen_markets:
                raise serializers.ValidationError(
                    f'No puedes combinar dos selecciones del mismo mercado ({market.name}).'
                )
            seen_markets[market.id] = sel
            allowed, message = can_bet_on_selection(sel)
            if not allowed:
                raise serializers.ValidationError(message)
        return selections

    def validate_stake(self, stake):
        if stake > settings.MAX_BET_STAKE:
            raise serializers.ValidationError('El monto supera el límite máximo por apuesta.')
        return stake

    def validate(self, data):
        user = self.context['request'].user
        if user.account_status != AccountStatus.VERIFICADO:
            raise serializers.ValidationError('Tu cuenta debe estar verificada para apostar.')

        stake = data['stake']
        for sel in data['selections']:
            allowed, message = can_bet_on_selection(sel, stake=stake)
            if not allowed:
                raise serializers.ValidationError(message)
        return data


class BetCreateSerializer(serializers.Serializer):
    selection = serializers.PrimaryKeyRelatedField(
        queryset=Selection.objects.select_related('market__event')
    )
    stake = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        min_value=Decimal('0.0001'),
    )
    odds_expected = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        min_value=Decimal('0.0001'),
        required=False,
        allow_null=True,
        help_text=(
            'Cuota que el usuario vio al abrir el ticket. '
            'Si las odds actuales difieren, se retorna 409 con las nuevas cuotas.'
        ),
    )

    def validate_stake(self, stake):
        if stake > settings.MAX_BET_STAKE:
            raise serializers.ValidationError('El monto supera el límite máximo por apuesta.')
        return stake

    def validate(self, data):
        user = self.context['request'].user
        if user.account_status != AccountStatus.VERIFICADO:
            raise serializers.ValidationError('Tu cuenta debe estar verificada para apostar.')

        selection = data['selection']
        stake = data['stake']
        allowed, message = can_bet_on_selection(selection, stake=stake)
        if not allowed:
            raise serializers.ValidationError(message)
        return data


class CashoutSerializer(serializers.Serializer):
    odds_actual = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        min_value=Decimal('0.0001'),
    )


class BetSerializer(serializers.ModelSerializer):
    selection = serializers.PrimaryKeyRelatedField(read_only=True)
    market = serializers.PrimaryKeyRelatedField(read_only=True)
    transaction_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Bet
        fields = ['id','market','selection','stake','odds','status','transaction_id','created_at',]
        read_only_fields = fields

class EventSettleSerializer(serializers.Serializer):
    result = serializers.CharField(
        max_length=150,
        help_text='Nombre exacto de la selección ganadora',
    )

    @property
    def winning_selection_name(self):
        return self.validated_data['result'].strip()
