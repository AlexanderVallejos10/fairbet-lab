from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile
from .validators import validate_adult_birth_date, validate_peruvian_dni


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    dni = serializers.CharField(max_length=8)
    birth_date = serializers.DateField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ese usuario ya existe.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ese correo ya existe.")
        return value

    def validate_dni(self, value):
        value = validate_peruvian_dni(value)

        if UserProfile.objects.filter(dni=value).exists():
            raise serializers.ValidationError("Ese DNI ya está registrado.")

        return value

    def validate_birth_date(self, value):
        return validate_adult_birth_date(value)

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        profile = UserProfile.objects.create(
            user=user,
            dni=validated_data["dni"],
            birth_date=validated_data["birth_date"],
            kyc_status=UserProfile.KYCStatus.PENDING,
        )

        return profile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "dni",
            "birth_date",
            "kyc_status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields