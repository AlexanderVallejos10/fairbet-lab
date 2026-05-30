from datetime import timedelta
from decimal import Decimal
import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from apps.users.choices import AccountStatus, ExclusionType
from apps.users.models import DepositLimitChange, SelfExclusion, User
from apps.users.validators import validate_dni, validate_mayoria_edad
from apps.wallet.models import AccountType
from apps.wallet.services import (_crear_par_balanceado,_get_account,_get_global_account,get_or_create_wallet,)
BONO_BIENVENIDA = Decimal('50.0000')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ['email', 'dni', 'first_name', 'last_name', 'birth_date', 'password']

    def validate_dni(self, value):
        validate_dni(value)
        return value

    def validate_birth_date(self, value):
        validate_mayoria_edad(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')

        with transaction.atomic():
            user = User(**validated_data)
            user.set_password(password)
            user.save()
            get_or_create_wallet(user)
            if not user.welcome_bonus_granted:
                cuenta_usuario = _get_account(user, AccountType.WALLET_USUARIO)
                cuenta_bonos = _get_global_account(AccountType.BONOS)

                _crear_par_balanceado(
                    cuenta_origen=cuenta_bonos,
                    cuenta_destino=cuenta_usuario,
                    amount=BONO_BIENVENIDA,
                    description='Bono de bienvenida',
                    transaction_id=uuid.uuid4(),
                )

                user.welcome_bonus_granted = True
                user.save(update_fields=['welcome_bonus_granted'])

        return user

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'dni', 'first_name', 'last_name',
            'birth_date', 'account_status',
            'deposit_limit_daily', 'deposit_limit_weekly',
            'deposit_limit_monthly', 'welcome_bonus_granted',
            'date_joined',
        ]
        read_only_fields = [
            'id', 'email', 'dni', 'account_status',
            'welcome_bonus_granted', 'date_joined',
        ]

class DepositLimitSerializer(serializers.Serializer):
    field_name = serializers.ChoiceField(
        choices=['deposit_limit_daily', 'deposit_limit_weekly', 'deposit_limit_monthly'],
    )
    new_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True, required=False, default=None,
    )

    def validate(self, data):
        user = self.context['request'].user
        field_name = data['field_name']
        new_value = data.get('new_value')
        current_value = getattr(user, field_name)
        raising = current_value is not None and (new_value is None or new_value > current_value)
        if raising and user.deposit_limit_updated_at:
            cooldown_end = user.deposit_limit_updated_at + timedelta(hours=24)
            if timezone.now() < cooldown_end:
                remaining = int((cooldown_end - timezone.now()).total_seconds() / 60)
                raise serializers.ValidationError(
                    f'Debe esperar {remaining} minutos para subir este límite.',
                )
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        field_name = validated_data['field_name']
        new_value = validated_data.get('new_value')
        current_value = getattr(user, field_name)
        DepositLimitChange.objects.create(
            user=user, field_name=field_name,
            old_value=current_value, new_value=new_value,
        )
        setattr(user, field_name, new_value)
        user.deposit_limit_updated_at = timezone.now()
        user.save(update_fields=[field_name, 'deposit_limit_updated_at'])
        return user

class SelfExclusionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfExclusion
        fields = ['exclusion_type']

    def validate(self, data):
        user = self.context['request'].user
        if user.account_status == 'autoexcluido':
            raise serializers.ValidationError('El usuario ya se encuentra autoexcluido.')
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        exclusion_type = validated_data['exclusion_type']
        start = timezone.now()
        periods = {
            ExclusionType.TEMPORAL_7: timedelta(days=7),
            ExclusionType.TEMPORAL_30: timedelta(days=30),
            ExclusionType.TEMPORAL_90: timedelta(days=90),
        }
        end = start + periods[exclusion_type] if exclusion_type in periods else None
        exclusion = SelfExclusion.objects.create(
            user=user, exclusion_type=exclusion_type,
            start_date=start, end_date=end,
        )
        user.account_status = 'autoexcluido'
        user.save(update_fields=['account_status'])
        return exclusion

class VerifyAccountSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)

    def validate_user_id(self, value):
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError('Usuario no encontrado.') from exc
        if user.account_status == AccountStatus.VERIFICADO:
            raise serializers.ValidationError('La cuenta ya se encuentra verificada.')
        if user.account_status == AccountStatus.AUTOEXCLUIDO:
            raise serializers.ValidationError(
                'No se puede verificar una cuenta autoexcluida.',
            )
        return value

    def create(self, validated_data):
        user = User.objects.get(pk=validated_data['user_id'])
        user.account_status = AccountStatus.VERIFICADO
        user.save(update_fields=['account_status'])
        return user