from datetime import date

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class DocumentType(models.TextChoices):
        DNI = "dni", "DNI"
        CE = "ce", "Carnet de extranjería"
        PASSPORT = "pasaporte", "Pasaporte"

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
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.DNI,
    )
    document_number = models.CharField(max_length=20)
    birth_date = models.DateField()
    kyc_status = models.CharField(
        max_length=32,
        choices=KYCStatus.choices,
        default=KYCStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document_type", "document_number"],
                name="uniq_user_profile_document",
            )
        ]

    @property
    def is_adult(self) -> bool:
        today = date.today()
        age = today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
        return age >= 18

    def __str__(self) -> str:
        return f"{self.user.username} - {self.document_type} {self.document_number}"