import pytest

from apps.audit.models import AuditLog
from apps.audit.services import append_audit_log, verify_audit_chain


pytestmark = pytest.mark.django_db


def test_append_audit_log_creates_hash_chain():
    first = append_audit_log({"action": "deposit", "amount": "10"})
    second = append_audit_log({"action": "bet", "amount": "5"})

    assert first.current_hash
    assert second.previous_hash == first.current_hash
    assert len(first.current_hash) == 64
    assert len(second.current_hash) == 64


def test_verify_audit_chain_is_valid_then_detects_tamper():
    first = append_audit_log({"action": "deposit", "amount": "10"})
    second = append_audit_log({"action": "bet", "amount": "5"})

    result = verify_audit_chain()
    assert result["valid"] is True
    assert result["broken_index"] is None

    AuditLog.objects.filter(pk=first.pk).update(payload={"action": "tampered", "amount": "999"})
    tampered = verify_audit_chain()

    assert tampered["valid"] is False
    assert tampered["broken_index"] == 0
