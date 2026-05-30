from django.contrib import admin

from .models import Account, LedgerEntry


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "created_at")
    list_filter = ("type",)
    search_fields = ("user__username", "user__email")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "account", "direction", "amount", "created_at")
    list_filter = ("direction", "account__type")
    search_fields = ("transaction_id", "account__user__username")
