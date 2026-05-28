from django.urls import path

from .views import BetListView, EventListView, PlaceBetView, SettleEventView

app_name = "betting"

urlpatterns = [
    path("events/", EventListView.as_view(), name="events"),
    path("bets/", BetListView.as_view(), name="bets"),
    path("place/", PlaceBetView.as_view(), name="place"),
    path("events/<int:event_id>/settle/", SettleEventView.as_view(), name="settle-event"),
]