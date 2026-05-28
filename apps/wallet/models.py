from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Sum


class WalletAccount(models.Model):
    class AccountType(models.TextChoices):
        WALLET_USUARIO = "wallet_usuario", "Wallet usuario"
        CASA = "casa", "Casa"
        APUESTAS_PENDIENTES = "apuestas_pendientes", "Apuestas pendientes"
        BONOS = "bonos", "Bonos"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet_accounts",
    )
    account_type = models.CharField(max_length=32, choices=AccountType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "account_type"],
                name="uniq_wallet_account_user_type",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.account_type}"

    @property
    def balance(self) -> Decimal:
        credits = (
            self.entries.filter(direction=LedgerEntry.Direction.CREDIT)
            .aggregate(total=Sum("amount"))
            .get("total")
            or Decimal("0")
        )
        debits = (
            self.entries.filter(direction=LedgerEntry.Direction.DEBIT)
            .aggregate(total=Sum("amount"))
            .get("total")
            or Decimal("0")
        )
        return credits - debits


class LedgerTransaction(models.Model):
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.transaction_id)


class LedgerEntry(models.Model):
    class Direction(models.TextChoices):
        DEBIT = "DEBIT", "Debit"
        CREDIT = "CREDIT", "Credit"

    transaction = models.ForeignKey(
        LedgerTransaction,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    account = models.ForeignKey(
        WalletAccount,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    direction = models.CharField(max_length=6, choices=Direction.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.account} - {self.direction} - {self.amount}"


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=120, unique=True)
    transaction = models.ForeignKey(
        LedgerTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_keys",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.key