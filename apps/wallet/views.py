from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WalletAccount
from .serializers import WalletAccountSerializer, WalletActionSerializer
from .services import (
    deposit_virtual_chips,
    ensure_user_accounts,
    withdraw_virtual_chips,
)


class WalletSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        accounts_map = ensure_user_accounts(request.user)
        accounts = [
            accounts_map[WalletAccount.AccountType.WALLET_USUARIO],
            accounts_map[WalletAccount.AccountType.APUESTAS_PENDIENTES],
            accounts_map[WalletAccount.AccountType.BONOS],
        ]
        return Response(
            {
                "accounts": WalletAccountSerializer(accounts, many=True).data,
            }
        )


class DepositView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WalletActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx = deposit_virtual_chips(
            user=request.user,
            amount=serializer.validated_data["amount"],
            idempotency_key=serializer.validated_data["idempotency_key"],
        )

        return Response(
            {
                "message": "Depósito simulado realizado correctamente.",
                "transaction_id": str(tx.transaction_id),
            },
            status=status.HTTP_201_CREATED,
        )


class WithdrawView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WalletActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx = withdraw_virtual_chips(
            user=request.user,
            amount=serializer.validated_data["amount"],
            idempotency_key=serializer.validated_data["idempotency_key"],
        )

        return Response(
            {
                "message": "Retiro simulado realizado correctamente.",
                "transaction_id": str(tx.transaction_id),
            },
            status=status.HTTP_201_CREATED,
        )
