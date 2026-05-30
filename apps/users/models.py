from django.conf import settings
from django.db import models

from .choices import EstadoKYC


class PerfilUsuario(models.Model):
    class KYCStatus(models.TextChoices):
        PENDING = EstadoKYC.PENDIENTE, "Pendiente de verificacion"
        VERIFIED = EstadoKYC.VERIFICADO, "Verificado"
        BLOCKED = EstadoKYC.BLOQUEADO, "Bloqueado"
        SELF_EXCLUDED = EstadoKYC.AUTOEXCLUIDO, "Autoexcluido"

    class DocumentType(models.TextChoices):
        DNI = "dni", "DNI"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    dni = models.CharField(max_length=8, unique=True)
    fecha_nacimiento = models.DateField()
    estado_kyc = models.CharField(
        max_length=32,
        choices=EstadoKYC.choices,
        default=EstadoKYC.PENDIENTE,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        return f"{self.user.username} - {self.dni}"

    @property
    def es_mayor_de_edad(self):
        from datetime import date

        hoy = date.today()
        edad = hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
        return edad >= 18

    @property
    def document_number(self):
        return self.dni

    @document_number.setter
    def document_number(self, value):
        self.dni = value

    @property
    def birth_date(self):
        return self.fecha_nacimiento

    @birth_date.setter
    def birth_date(self, value):
        self.fecha_nacimiento = value

    @property
    def kyc_status(self):
        return self.estado_kyc

    @kyc_status.setter
    def kyc_status(self, value):
        self.estado_kyc = value

    @property
    def created_at(self):
        return self.creado_en

    @property
    def updated_at(self):
        return self.actualizado_en


UserProfile = PerfilUsuario
