import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

class AccountType(models.TextChoices):
    WALLET_USUARIO = 'wallet_usuario', _('Wallet del usuario')
    CASA = 'casa', _('Casa')
    APUESTAS_PENDIENTES = 'apuestas_pendientes', _('Apuestas pendientes')
    BONOS = 'bonos', _('Bonos')

class Direction(models.TextChoices):
    DEBIT = 'DEBIT', _('Débito')
    CREDIT = 'CREDIT', _('Crédito')

class Account(models.Model):
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='accounts',
        verbose_name=_('usuario'),
    )
    type = models.CharField(
        max_length=25,
        choices=AccountType.choices,
        verbose_name=_('tipo de cuenta'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('creada en'),
    )

    class Meta:
        verbose_name = _('cuenta')
        verbose_name_plural = _('cuentas')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'type'],
                condition=models.Q(user__isnull=False),
                name='unique_account_per_user_type',
            ),
            models.UniqueConstraint(
                fields=['type'],
                condition=models.Q(user__isnull=True),
                name='unique_global_account_type',
            ),
        ]

    def __str__(self):
        if self.user:
            return f'{self.get_type_display()} — {self.user.email}'
        return f'{self.get_type_display()} (global)'


class LedgerEntry(models.Model):

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='entries',
        verbose_name=_('cuenta'),
    )
    amount = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        verbose_name=_('monto'),
    )
    direction = models.CharField(
        max_length=6,
        choices=Direction.choices,
        verbose_name=_('dirección'),
    )
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
        verbose_name=_('ID de transacción'),
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name=_('descripción'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('creado en'),
    )

    class Meta:
        verbose_name = _('entrada del libro mayor')
        verbose_name_plural = _('entradas del libro mayor')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'direction'], name='idx_ledger_account_direction'),
        ]

    def __str__(self):
        return f'{self.direction} {self.amount} — {self.account} [{self.transaction_id}]'
