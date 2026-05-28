from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog
from .serializers import AuditLogSerializer
from .services import append_audit_log, verify_audit_chain


class AuditLogListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        logs = AuditLog.objects.order_by("-created_at")
        return Response(AuditLogSerializer(logs, many=True).data)


class AuditCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        payload = request.data.get("payload", request.data)
        log = append_audit_log(payload)

        return Response(
            {
                "message": "Registro de auditoría creado correctamente.",
                "audit_log": AuditLogSerializer(log).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AuditVerifyView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        result = verify_audit_chain()
        return Response(result)