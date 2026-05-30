from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountType(models.TextChoices):
    WALLET_USUARIO = "wallet_usuario", _("Wallet del usuario")
    CASA = "casa", _("Casa")
    APUESTAS_PENDIENTES = "apuestas_pendientes", _("Apuestas pendientes")
    BONOS = "bonos", _("Bonos")


class Direction(models.TextChoices):
    DEBIT = "DEBIT", _("Debito")
    CREDIT = "CREDIT", _("Credito")


class Account(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="accounts",
        verbose_name=_("usuario"),
    )
    type = models.CharField(
        max_length=25,
        choices=AccountType.choices,
        verbose_name=_("tipo de cuenta"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("creada en"))

    class Meta:
        verbose_name = _("cuenta")
        verbose_name_plural = _("cuentas")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "type"],
                condition=models.Q(user__isnull=False),
                name="unique_account_per_user_type",
            ),
            models.UniqueConstraint(
                fields=["type"],
                condition=models.Q(user__isnull=True),
                name="unique_global_account_type",
            ),
        ]

    def __str__(self):
        if self.user:
            return f"{self.get_type_display()} - {self.user}"
        return f"{self.get_type_display()} (global)"

    @property
    def account_type(self):
        return self.type

    @account_type.setter
    def account_type(self, value):
        self.type = value

    @property
    def balance(self):
        creditos = sum(
            entry.amount for entry in self.entries.all() if entry.direction == Direction.CREDIT
        )
        debitos = sum(
            entry.amount for entry in self.entries.all() if entry.direction == Direction.DEBIT
        )
        return creditos - debitos


class LedgerEntry(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name=_("cuenta"),
    )
    amount = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        verbose_name=_("monto"),
    )
    direction = models.CharField(
        max_length=6,
        choices=Direction.choices,
        verbose_name=_("direccion"),
    )
    transaction_id = models.CharField(
        max_length=120,
        db_index=True,
        verbose_name=_("ID de transaccion"),
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("descripcion"),
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("creado en"))

    class Meta:
        verbose_name = _("entrada del libro mayor")
        verbose_name_plural = _("entradas del libro mayor")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account", "direction"], name="idx_ledger_account_direction"),
        ]

    def __str__(self):
        return f"{self.direction} {self.amount} - {self.account} [{self.transaction_id}]"


Account.AccountType = AccountType
WalletAccount = Account
