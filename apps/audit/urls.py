from django.urls import path

from .views import AuditCreateView, AuditLogListView, AuditVerifyView

app_name = "audit"

urlpatterns = [
    path("", AuditLogListView.as_view(), name="list"),
    path("create/", AuditCreateView.as_view(), name="create"),
    path("verify/", AuditVerifyView.as_view(), name="verify"),
]