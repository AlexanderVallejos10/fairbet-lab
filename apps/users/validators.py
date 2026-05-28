from datetime import date

from django.core.exceptions import ValidationError


def validate_peruvian_dni(value: str) -> str:
    value = value.strip()

    if not value.isdigit():
        raise ValidationError("El DNI debe contener solo números.")

    if len(value) != 8:
        raise ValidationError("El DNI debe tener 8 dígitos.")

    if value == "00000000":
        raise ValidationError("El DNI no es válido.")

    return value


def validate_adult_birth_date(value):
    today = date.today()

    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

    if age < 18:
        raise ValidationError("El usuario debe ser mayor de edad.")

    return value