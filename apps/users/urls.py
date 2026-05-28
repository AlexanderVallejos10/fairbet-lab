from django.urls import path

from .views import MyProfileView, RegisterView

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MyProfileView.as_view(), name="me"),
]