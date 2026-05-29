import pytest


@pytest.fixture
def usuario_base():
    return {
        "username": "usuario_prueba",
        "email": "usuario@correo.com",
        "password": "Clave12345",
        "dni": "12345678",
    }