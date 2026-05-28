from decimal import Decimal

from rest_framework import serializers

from .models import WalletAccount


class WalletActionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    idempotency_key = serializers.CharField(max_length=120)


class WalletAccountSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = WalletAccount
        fields = ("id", "account_type", "balance", "created_at")

    def get_balance(self, obj):
        return obj.balance