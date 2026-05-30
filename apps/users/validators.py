from datetime import date

from django.core.exceptions import ValidationError


def validar_fecha_mayoria_edad(fecha_nacimiento):
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

    if edad < 18:
        raise ValidationError("El usuario debe ser mayor de edad.")

    return fecha_nacimiento


def validar_dni_peruano(valor):
    valor = str(valor).strip()

    if not valor.isdigit():
        raise ValidationError("El DNI debe contener solo números.")

    if len(valor) != 8:
        raise ValidationError("El DNI debe tener 8 dígitos.")

    if valor == "00000000":
        raise ValidationError("El DNI no es válido.")

    if len(set(valor)) == 1:
        raise ValidationError("El DNI no puede tener todos los digitos iguales.")

    return valor


def validate_adult_birth_date(fecha_nacimiento):
    return validar_fecha_mayoria_edad(fecha_nacimiento)


def validate_peruvian_dni(valor):
    return validar_dni_peruano(valor)


def validate_document_number(document_type, document_number):
    if document_type != "dni":
        raise ValidationError("Solo se admite DNI peruano.")
    return validar_dni_peruano(document_number)
