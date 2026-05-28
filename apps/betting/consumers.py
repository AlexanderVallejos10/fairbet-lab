from channels.generic.websocket import AsyncJsonWebsocketConsumer


class LiveOddsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope["url_route"]["kwargs"]["event_id"]
        self.group_name = f"event_{self.event_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def odds_update(self, event):
        await self.send_json(
            {
                "type": "odds_update",
                "event_id": event["event_id"],
                "odd_id": event["odd_id"],
                "selection": event["selection"],
                "decimal_odds": event["decimal_odds"],
                "is_active": event["is_active"],
            }
        )