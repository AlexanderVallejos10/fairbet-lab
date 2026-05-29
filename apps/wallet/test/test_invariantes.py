from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.wallet.services import deposit, get_balance, get_or_create_wallet, reserve_for_bet

User = get_user_model()


@pytest.fixture
def usuario(db):
    return User.objects.create_user(
        username="usuario_invariante",
        email="invariante@correo.com",
        password="Clave12345",
    )


@pytest.mark.django_db
def test_saldo_cero_inicial(usuario):
    get_or_create_wallet(usuario)
    assert get_balance(usuario) == Decimal("0")


@pytest.mark.django_db
def test_saldo_calculado_desde_movimientos(usuario):
    get_or_create_wallet(usuario)
    deposit(usuario, Decimal("300.0000"))
    reserve_for_bet(usuario, Decimal("100.0000"))
    assert get_balance(usuario) == Decimal("200.0000")


@pytest.mark.django_db
def test_monto_con_decimal_exacto(usuario):
    get_or_create_wallet(usuario)
    deposit(usuario, Decimal("50.1234"))
    assert get_balance(usuario) == Decimal("50.1234")