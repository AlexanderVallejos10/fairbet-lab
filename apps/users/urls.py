from django.urls import path

from .views import PerfilActualView, RegistroView

urlpatterns = [
    path("register/", RegistroView.as_view(), name="users-register"),
    path("me/", PerfilActualView.as_view(), name="users-me"),
]