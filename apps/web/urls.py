from django.urls import path

from .views import (
    add_to_coupon,
    clear_coupon,
    dashboard_page,
    events_page,
    home,
    history_page,
    login_page,
    place_coupon_bet,
    profile_page,
    register_page,
    sync_coupon,
    wallet_page,
)

app_name = "web"

urlpatterns = [
    path("", home, name="home"),
    path("events/", events_page, name="events"),
    path("events/add/<int:odd_id>/", add_to_coupon, name="add_to_coupon"),
    path("events/sync/", sync_coupon, name="sync_coupon"),
    path("events/place/", place_coupon_bet, name="place_coupon_bet"),
    path("events/clear/", clear_coupon, name="clear_coupon"),
    path("login/", login_page, name="login"),
    path("register/", register_page, name="register"),
    path("wallet/", wallet_page, name="wallet"),
    path("historial/", history_page, name="history"),
    path("perfil/", profile_page, name="profile"),
    path("dashboard/", dashboard_page, name="dashboard"),
]