from django.contrib import admin

from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "dni", "fecha_nacimiento", "estado_kyc", "creado_en")
    search_fields = ("user__username", "user__email", "dni")
    list_filter = ("estado_kyc",)