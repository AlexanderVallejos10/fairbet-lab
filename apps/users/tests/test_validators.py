import pytest
from django.core.exceptions import ValidationError

from apps.users.validators import validar_dni_peruano, validar_fecha_mayoria_edad


def test_validar_dni_peruano_acepta_8_digitos():
    assert validar_dni_peruano("12345678") == "12345678"


def test_validar_dni_peruano_rechaza_letras():
    with pytest.raises(ValidationError):
        validar_dni_peruano("12A45678")


def test_validar_fecha_mayoria_edad_rechaza_menor():
    from datetime import date

    fecha = date.today().replace(year=date.today().year - 17)
    with pytest.raises(ValidationError):
        validar_fecha_mayoria_edad(fecha)