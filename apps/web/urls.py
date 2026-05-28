from django.urls import path

from .views import dashboard_page, history_page, home, login_page, profile_page, register_page, wallet_page

app_name = "web"

urlpatterns = [
    path("", home, name="home"),
    path("login/", login_page, name="login"),
    path("register/", register_page, name="register"),
    path("wallet/", wallet_page, name="wallet"),
    path("historial/", history_page, name="history"),
    path("perfil/", profile_page, name="profile"),
    path("dashboard/", dashboard_page, name="dashboard"),
]