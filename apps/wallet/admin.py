from django.contrib import admin

from .models import IdempotencyKey, LedgerEntry, LedgerTransaction, WalletAccount


@admin.register(WalletAccount)
class WalletAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "account_type", "created_at")
    list_filter = ("account_type",)
    search_fields = ("user__username", "user__email")


@admin.register(LedgerTransaction)
class LedgerTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "description", "created_at")
    search_fields = ("transaction_id", "description")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("transaction", "account", "direction", "amount", "created_at")
    list_filter = ("direction", "account__account_type")
    search_fields = ("transaction__transaction_id", "account__user__username")


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "transaction", "created_at")
    search_fields = ("key",)