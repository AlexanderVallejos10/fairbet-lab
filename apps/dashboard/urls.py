from django.urls import path
from .views import OperatorDashboardView

app_name = "dashboard"

urlpatterns = [
    path("operator/", OperatorDashboardView.as_view(), name="operator"),
]