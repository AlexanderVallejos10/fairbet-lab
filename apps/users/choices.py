from django.db import models


class EstadoKYC(models.TextChoices):
    PENDIENTE = "pendiente_verificacion", "Pendiente de verificación"
    VERIFICADO = "verificado", "Verificado"
    BLOQUEADO = "bloqueado", "Bloqueado"
    AUTOEXCLUIDO = "autoexcluido", "Autoexcluido"


AccountStatus = EstadoKYC
