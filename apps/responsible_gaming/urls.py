from django.urls import path

from .views import DepositLimitView, SelfExclusionView

app_name = "responsible_gaming"

urlpatterns = [
    path("limits/", DepositLimitView.as_view(), name="limits"),
    path("self-exclusion/", SelfExclusionView.as_view(), name="self-exclusion"),
]