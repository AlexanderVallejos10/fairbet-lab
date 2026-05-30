import json
from channels.generic.websocket import AsyncWebsocketConsumer

def _group_name(event_id):
    return f"odds-event-{event_id}"

class OddsConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.event_id = self.scope["url_route"]["kwargs"].get("event_id")
        self.room_group_name = _group_name(self.event_id)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def odds_update(self, event):
        """
        Envía al cliente las cuotas actualizadas del evento.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "odds_update",
                    "event_id": event["event_id"],
                    "selections": event["selections"],
                }
            )
        )

async def broadcast_odds_update(event_id, selections):
    
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()

    await channel_layer.group_send(
        _group_name(event_id),
        {
            "type": "odds.update",
            "event_id": event_id,
            "selections": selections,
        },
    )