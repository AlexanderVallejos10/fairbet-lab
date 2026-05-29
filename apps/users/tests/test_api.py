import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_registro_usuario():
    cliente = APIClient()
    respuesta = cliente.post(
        "/api/users/register/",
        {
            "username": "nuevo_usuario",
            "email": "nuevo@correo.com",
            "password": "Clave12345",
            "dni": "12345678",
            "fecha_nacimiento": "1995-01-01",
        },
        format="json",
    )
    assert respuesta.status_code == 201