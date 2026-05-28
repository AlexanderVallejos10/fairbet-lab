from django.urls import path

from .views import (
    BetListView,
    CashOutBetView,
    CombinedBetListView,
    EventListView,
    PlaceBetView,
    PlaceCombinedBetView,
    SettleEventView,
)

app_name = "betting"

urlpatterns = [
    path("events/", EventListView.as_view(), name="events"),
    path("bets/", BetListView.as_view(), name="bets"),
    path("combined/", CombinedBetListView.as_view(), name="combined"),
    path("place/", PlaceBetView.as_view(), name="place"),
    path("combined/place/", PlaceCombinedBetView.as_view(), name="place-combined"),
    path("bets/<int:bet_id>/cashout/", CashOutBetView.as_view(), name="cashout-bet"),
    path("events/<int:event_id>/settle/", SettleEventView.as_view(), name="settle-event"),
]