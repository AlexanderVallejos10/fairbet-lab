from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Odd


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