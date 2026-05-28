from django.urls import path

from .views import DepositView, WalletSummaryView, WithdrawView

app_name = "wallet"

urlpatterns = [
    path("summary/", WalletSummaryView.as_view(), name="summary"),
    path("deposit/", DepositView.as_view(), name="deposit"),
    path("withdraw/", WithdrawView.as_view(), name="withdraw"),
]