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

    return valor