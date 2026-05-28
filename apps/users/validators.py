from datetime import date

from django.core.exceptions import ValidationError


def validate_adult_birth_date(value):
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

    if age < 18:
        raise ValidationError("El usuario debe ser mayor de edad.")

    return value


def _normalize_document_number(value: str) -> str:
    return value.strip().upper()


def _validate_dni(value: str) -> str:
    value = _normalize_document_number(value)

    if not value.isdigit():
        raise ValidationError("El DNI debe contener solo números.")

    if len(value) != 8:
        raise ValidationError("El DNI debe tener 8 dígitos.")

    if value == "00000000":
        raise ValidationError("El DNI no es válido.")

    digits = [int(x) for x in value]
    checksum = sum(digits[:7]) % 10

    if digits[7] != checksum:
        raise ValidationError("El DNI no pasa la validación básica.")

    return value


def _validate_foreign_document(value: str) -> str:
    value = _normalize_document_number(value)

    if len(value) < 6 or len(value) > 12:
        raise ValidationError("El documento debe tener entre 6 y 12 caracteres.")

    if not any(ch.isdigit() for ch in value):
        raise ValidationError("El documento debe contener al menos un número.")

    if not value.isalnum():
        raise ValidationError("El documento solo puede contener letras y números.")

    return value


def validate_document_number(document_type: str, value: str) -> str:
    if document_type == "dni":
        return _validate_dni(value)

    return _validate_foreign_document(value)

def validate_peruvian_dni(value: str) -> str:
    return validate_document_number("dni", value)