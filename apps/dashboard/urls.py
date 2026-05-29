from django.urls import path

from .views import panel_dashboard, reporte_mensual_csv

app_name = "dashboard"

urlpatterns = [
    path("", panel_dashboard, name="panel"),
    path("reporte.csv", reporte_mensual_csv, name="reporte-csv"),
]