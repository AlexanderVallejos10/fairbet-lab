from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "dni", "birth_date", "kyc_status", "created_at")
    search_fields = ("user__username", "dni", "user__email")
    list_filter = ("kyc_status",)