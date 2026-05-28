from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile
from .validators import (
    validate_adult_birth_date,
    validate_document_number,
)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.ChoiceField(choices=UserProfile.DocumentType.choices)
    document_number = serializers.CharField(max_length=20)
    birth_date = serializers.DateField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ese usuario ya existe.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ese correo ya existe.")
        return value

    def validate(self, attrs):
        attrs["document_number"] = validate_document_number(
            attrs["document_type"],
            attrs["document_number"],
        )
        attrs["birth_date"] = validate_adult_birth_date(attrs["birth_date"])
        return attrs

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
            document_type=validated_data["document_type"],
            document_number=validated_data["document_number"],
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
            "document_type",
            "document_number",
            "birth_date",
            "kyc_status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields