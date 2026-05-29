from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import PerfilUsuario
from .validators import validar_dni_peruano, validar_fecha_mayoria_edad

User = get_user_model()


class RegistroSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    dni = serializers.CharField(max_length=8)
    fecha_nacimiento = serializers.DateField()

    def validate_username(self, valor):
        if User.objects.filter(username=valor).exists():
            raise serializers.ValidationError("Ese usuario ya existe.")
        return valor

    def validate_email(self, valor):
        if User.objects.filter(email=valor).exists():
            raise serializers.ValidationError("Ese correo ya existe.")
        return valor

    def validate(self, attrs):
        attrs["dni"] = validar_dni_peruano(attrs["dni"])
        attrs["fecha_nacimiento"] = validar_fecha_mayoria_edad(attrs["fecha_nacimiento"])
        return attrs

    def create(self, validated_data):
        usuario = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        perfil = PerfilUsuario.objects.create(
            user=usuario,
            dni=validated_data["dni"],
            fecha_nacimiento=validated_data["fecha_nacimiento"],
            estado_kyc="pendiente_verificacion",
        )
        return perfil


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = (
            "id",
            "username",
            "email",
            "dni",
            "fecha_nacimiento",
            "estado_kyc",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = fields