from django.conf import settings
from django.db import models

from .validators import validate_adult_birth_date, validate_peruvian_dni


class UserProfile(models.Model):
    class KYCStatus(models.TextChoices):
        PENDING = "pendiente_verificacion", "Pendiente de verificación"
        VERIFIED = "verificado", "Verificado"
        BLOCKED = "bloqueado", "Bloqueado"
        SELF_EXCLUDED = "autoexcluido", "Autoexcluido"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    dni = models.CharField(
        max_length=8,
        unique=True,
        validators=[validate_peruvian_dni],
    )
    birth_date = models.DateField(
        validators=[validate_adult_birth_date],
    )
    kyc_status = models.CharField(
        max_length=32,
        choices=KYCStatus.choices,
        default=KYCStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_adult(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"{self.user.username} - {self.dni}"