from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "previous_hash", "current_hash", "created_at")
    search_fields = ("previous_hash", "current_hash")
    readonly_fields = ("previous_hash", "payload", "current_hash", "created_at")
