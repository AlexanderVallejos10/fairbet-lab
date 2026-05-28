from decimal import Decimal

from rest_framework import serializers

from .models import DepositLimit, SelfExclusion


class DepositLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositLimit
        fields = (
            "daily_limit",
            "weekly_limit",
            "monthly_limit",
            "pending_daily_limit",
            "pending_weekly_limit",
            "pending_monthly_limit",
            "limit_change_available_at",
        )
        read_only_fields = (
            "pending_daily_limit",
            "pending_weekly_limit",
            "pending_monthly_limit",
            "limit_change_available_at",
        )


class UpdateDepositLimitSerializer(serializers.Serializer):
    daily_limit = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)
    weekly_limit = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)
    monthly_limit = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)


class SelfExcludeSerializer(serializers.Serializer):
    duration = serializers.ChoiceField(choices=SelfExclusion.Duration.choices)