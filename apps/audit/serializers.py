from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id", "previous_hash", "payload", "current_hash", "created_at")
        read_only_fields = fields


class VerifyAuditChainSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    total_logs = serializers.IntegerField()
    broken_index = serializers.IntegerField(allow_null=True)