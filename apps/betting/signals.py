from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.services import append_audit_log

from .models import Bet, CombinedBet, Odd


@receiver(post_save, sender=Odd)
def broadcast_odd_change(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    def _send():
        async_to_sync(channel_layer.group_send)(
            f"event_{instance.event_id}",
            {
                "type": "odds_update",
                "event_id": instance.event_id,
                "odd_id": instance.id,
                "selection": instance.selection,
                "decimal_odds": str(instance.decimal_odds),
                "is_active": instance.is_active,
            },
        )

    transaction.on_commit(_send)

    def _append_audit():
        append_audit_log(
            {
                "type": "betting.odd.saved",
                "odd_id": instance.id,
                "event_id": instance.event_id,
                "selection": instance.selection,
                "decimal_odds": str(instance.decimal_odds),
                "is_active": instance.is_active,
                "created": created,
            }
        )

    transaction.on_commit(_append_audit)


@receiver(post_save, sender=Bet)
def audit_bet_change(sender, instance, created, **kwargs):
    def _append():
        append_audit_log(
            {
                "type": "betting.bet.created" if created else "betting.bet.updated",
                "bet_id": instance.id,
                "user_id": instance.user_id,
                "event_id": instance.event_id,
                "odd_id": instance.odd_id,
                "stake": str(instance.stake),
                "odds_snapshot": str(instance.odds_snapshot),
                "status": instance.status,
                "payout": str(instance.payout),
                "transaction_id": str(instance.transaction_id),
                "idempotency_key": instance.idempotency_key,
            }
        )

    transaction.on_commit(_append)


@receiver(post_save, sender=CombinedBet)
def audit_combined_bet_change(sender, instance, created, **kwargs):
    def _append():
        append_audit_log(
            {
                "type": "betting.combined_bet.created" if created else "betting.combined_bet.updated",
                "combined_bet_id": instance.id,
                "user_id": instance.user_id,
                "stake": str(instance.stake),
                "odds_snapshot": str(instance.odds_snapshot),
                "selection_count": instance.selection_count,
                "status": instance.status,
                "payout": str(instance.payout),
                "transaction_id": str(instance.transaction_id),
                "idempotency_key": instance.idempotency_key,
            }
        )

    transaction.on_commit(_append)
