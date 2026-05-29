from decimal import Decimal

from rest_framework import serializers

from apps.users.choices import AccountStatus


def _estado_kyc_usuario(usuario):
    if hasattr(usuario, "account_status"):
        return usuario.account_status
    perfil = getattr(usuario, "perfil", None) or getattr(usuario, "profile", None)
    if perfil:
        return getattr(perfil, "estado_kyc", None) or getattr(perfil, "kyc_status", None)
    return None


def _limite_usuario(usuario, campo):
    if hasattr(usuario, campo):
        return getattr(usuario, campo)
    perfil = getattr(usuario, "perfil", None) or getattr(usuario, "profile", None)
    if perfil and hasattr(perfil, campo):
        return getattr(perfil, campo)
    return None


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    idempotency_key = serializers.UUIDField(required=False, default=None)

    def validate(self, data):
        user = self.context["request"].user
        estado = _estado_kyc_usuario(user)

        if estado not in [AccountStatus.VERIFICADO, "verificado"]:
            raise serializers.ValidationError(
                "Tu cuenta debe estar verificada para realizar depósitos."
            )

        limit_map = {
            "deposit_limit_daily": "diario",
            "deposit_limit_weekly": "semanal",
            "deposit_limit_monthly": "mensual",
        }
        for field, label in limit_map.items():
            limit = _limite_usuario(user, field)
            if limit is not None and data["amount"] > limit:
                raise serializers.ValidationError(
                    f"El monto supera tu límite {label} de depósito ({limit})."
                )

        return data


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    idempotency_key = serializers.UUIDField(required=False, default=None)

    def validate(self, data):
        user = self.context["request"].user
        estado = _estado_kyc_usuario(user)

        if estado not in [AccountStatus.VERIFICADO, "verificado"]:
            raise serializers.ValidationError(
                "Tu cuenta debe estar verificada para realizar retiros."
            )

        return data


class BalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=18, decimal_places=4)
    currency = serializers.CharField(default="fichas")