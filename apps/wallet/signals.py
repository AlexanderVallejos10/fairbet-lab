from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.services import append_audit_log

from .models import LedgerEntry


@receiver(post_save, sender=LedgerEntry)
def audit_ledger_entry(sender, instance, created, **kwargs):
    if not created:
        return

    def _append():
        append_audit_log(
            {
                "type": "wallet.ledger_entry.created",
                "ledger_entry_id": instance.id,
                "account_id": instance.account_id,
                "amount": str(instance.amount),
                "direction": instance.direction,
                "transaction_id": str(instance.transaction_id),
                "description": instance.description,
            }
        )

    transaction.on_commit(_append)
