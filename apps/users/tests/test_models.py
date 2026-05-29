import pytest
from django.contrib.auth import get_user_model
from apps.users.models import PerfilUsuario

User = get_user_model()


@pytest.mark.django_db
def test_crea_perfil_usuario():
    usuario = User.objects.create_user(
        username="juan",
        email="juan@correo.com",
        password="123456",
    )
    perfil = PerfilUsuario.objects.create(
        user=usuario,
        dni="12345678",
        fecha_nacimiento="1995-01-01",
    )
    assert perfil.user.username == "juan"
    assert perfil.dni == "12345678"