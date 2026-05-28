from django.contrib import admin

from .models import DepositLimit, SelfExclusion


@admin.register(DepositLimit)
class DepositLimitAdmin(admin.ModelAdmin):
    list_display = ("user", "daily_limit", "weekly_limit", "monthly_limit", "limit_change_available_at")
    search_fields = ("user__username",)


@admin.register(SelfExclusion)
class SelfExclusionAdmin(admin.ModelAdmin):
    list_display = ("user", "duration", "active", "starts_at", "ends_at")
    list_filter = ("active", "duration")
    search_fields = ("user__username",)