import hashlib
import json

from django.db import transaction

from .models import AuditLog


def _normalize_payload(payload) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def calculate_hash(previous_hash: str, payload) -> str:
    raw = f"{previous_hash}{_normalize_payload(payload)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@transaction.atomic
def append_audit_log(payload: dict) -> AuditLog:
    last_log = AuditLog.objects.order_by("-id").first()
    previous_hash = last_log.current_hash if last_log else ""

    current_hash = calculate_hash(previous_hash, payload)

    return AuditLog.objects.create(
        previous_hash=previous_hash,
        payload=payload,
        current_hash=current_hash,
    )


def verify_audit_chain() -> dict:
    logs = list(AuditLog.objects.order_by("id"))

    previous_hash = ""
    broken_index = None

    for index, log in enumerate(logs):
        expected_hash = calculate_hash(previous_hash, log.payload)

        if log.previous_hash != previous_hash or log.current_hash != expected_hash:
            broken_index = index
            break

        previous_hash = log.current_hash

    if broken_index is None:
        return {
            "valid": True,
            "total_logs": len(logs),
            "broken_index": None,
        }

    return {
        "valid": False,
        "total_logs": len(logs),
        "broken_index": broken_index,
    }