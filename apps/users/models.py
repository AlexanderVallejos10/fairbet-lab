from django.conf import settings
from django.db import models

from .choices import EstadoKYC


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
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