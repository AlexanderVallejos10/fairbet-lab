from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "document_type",
        "document_number",
        "birth_date",
        "kyc_status",
        "created_at",
    )
    search_fields = (
        "user__username",
        "document_number",
        "user__email",
    )
    list_filter = ("document_type", "kyc_status")