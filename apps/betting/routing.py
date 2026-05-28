from django.urls import path

from .consumers import LiveOddsConsumer

websocket_urlpatterns = [
    path("ws/betting/events/<int:event_id>/", LiveOddsConsumer.as_asgi()),
]