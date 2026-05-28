from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.betting.models import Bet


User = get_user_model()


class OperatorDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_staked = (
            Bet.objects.aggregate(total=Sum("stake")).get("total") or Decimal("0.0000")
        )
        total_paid = (
            Bet.objects.aggregate(total=Sum("payout")).get("total") or Decimal("0.0000")
        )

        ggr = total_staked - total_paid

        data = {
            "total_apostado": total_staked,
            "total_pagado": total_paid,
            "ggr": ggr,
            "cantidad_usuarios": User.objects.count(),
            "cantidad_apuestas": Bet.objects.count(),
        }
        return Response(data)