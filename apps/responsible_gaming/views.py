from drf_spectacular.openapi import AutoSchema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DepositLimit, SelfExclusion
from .serializers import DepositLimitSerializer, SelfExcludeSerializer, UpdateDepositLimitSerializer
from .services import (
    get_or_create_deposit_limit,
    is_self_excluded,
    lower_limits,
    request_limit_increase,
    self_exclude,
)


class DepositLimitView(APIView):
    schema = AutoSchema()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        limits = get_or_create_deposit_limit(request.user)
        return Response(DepositLimitSerializer(limits).data)

    def post(self, request):
        serializer = UpdateDepositLimitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current = get_or_create_deposit_limit(request.user)

        daily = serializer.validated_data.get("daily_limit")
        weekly = serializer.validated_data.get("weekly_limit")
        monthly = serializer.validated_data.get("monthly_limit")

        response_type = "updated"

        if (
            (daily is not None and current.daily_limit is not None and daily < current.daily_limit)
            or (weekly is not None and current.weekly_limit is not None and weekly < current.weekly_limit)
            or (monthly is not None and current.monthly_limit is not None and monthly < current.monthly_limit)
        ):
            limits = lower_limits(request.user, daily=daily, weekly=weekly, monthly=monthly)
            response_type = "lowered"
        else:
            limits = request_limit_increase(request.user, daily=daily, weekly=weekly, monthly=monthly)
            response_type = "pending_increase"

        return Response(
            {
                "message": "Límites actualizados correctamente.",
                "type": response_type,
                "limits": DepositLimitSerializer(limits).data,
            },
            status=status.HTTP_200_OK,
        )


class SelfExclusionView(APIView):
    schema = AutoSchema()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        exclusion = SelfExclusion.objects.filter(user=request.user).first()
        if not exclusion:
            return Response({"active": False})

        return Response(
            {
                "active": exclusion.active,
                "duration": exclusion.duration,
                "ends_at": exclusion.ends_at,
            }
        )

    def post(self, request):
        serializer = SelfExcludeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exclusion = self_exclude(request.user, serializer.validated_data["duration"])

        return Response(
            {
                "message": "Autoexclusión activada correctamente.",
                "active": exclusion.active,
                "duration": exclusion.duration,
                "ends_at": exclusion.ends_at,
            },
            status=status.HTTP_201_CREATED,
        )