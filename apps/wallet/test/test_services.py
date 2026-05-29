import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.wallet.models import AccountType
from apps.wallet.services import (
    SaldoInsuficiente,
    deposit,
    get_balance,
    get_or_create_wallet,
    reserve_for_bet,
    settle_loss,
    settle_win,
    withdraw,
)

User = get_user_model()


@pytest.fixture
def usuario(db):
    return User.objects.create_user(
        username="usuario_wallet",
        email="wallet@correo.com",
        password="Clave12345",
    )


@pytest.fixture
def usuario_con_saldo(usuario):
    get_or_create_wallet(usuario)
    deposit(usuario, Decimal("500.0000"))
    return usuario


@pytest.mark.django_db
def test_deposit_acredita_saldo(usuario):
    get_or_create_wallet(usuario)
    deposit(usuario, Decimal("200.0000"))
    assert get_balance(usuario) == Decimal("200.0000")


@pytest.mark.django_db
def test_deposit_idempotente(usuario):
    get_or_create_wallet(usuario)
    tid = uuid.uuid4()
    deposit(usuario, Decimal("100.0000"), transaction_id=tid)
    deposit(usuario, Decimal("100.0000"), transaction_id=tid)
    assert get_balance(usuario) == Decimal("100.0000")


@pytest.mark.django_db
def test_withdraw_descuenta_saldo(usuario_con_saldo):
    withdraw(usuario_con_saldo, Decimal("100.0000"))
    assert get_balance(usuario_con_saldo) == Decimal("400.0000")


@pytest.mark.django_db
def test_withdraw_saldo_insuficiente(usuario_con_saldo):
    with pytest.raises(SaldoInsuficiente):
        withdraw(usuario_con_saldo, Decimal("999.0000"))


@pytest.mark.django_db
def test_reserve_for_bet_descuenta_saldo(usuario_con_saldo):
    saldo_antes = get_balance(usuario_con_saldo)
    reserve_for_bet(usuario_con_saldo, Decimal("100.0000"))
    saldo_despues = get_balance(usuario_con_saldo)
    assert saldo_despues == saldo_antes - Decimal("100.0000")


@pytest.mark.django_db
def test_settle_win_acredita_payout_exacto(usuario_con_saldo):
    stake = Decimal("100.0000")
    odds = Decimal("2.5000")

    saldo_antes = get_balance(usuario_con_saldo)
    reserve_for_bet(usuario_con_saldo, stake)
    settle_win(usuario_con_saldo, stake, odds)
    saldo_despues = get_balance(usuario_con_saldo)

    assert saldo_despues == saldo_antes - stake + Decimal("250.0000")


@pytest.mark.django_db
def test_settle_loss_no_devuelve_stake(usuario_con_saldo):
    stake = Decimal("100.0000")

    saldo_antes = get_balance(usuario_con_saldo)
    reserve_for_bet(usuario_con_saldo, stake)
    settle_loss(usuario_con_saldo, stake)
    saldo_despues = get_balance(usuario_con_saldo)

    assert saldo_despues == saldo_antes - stake


@pytest.mark.django_db
def test_saldo_nunca_negativo(usuario_con_saldo):
    saldo = get_balance(usuario_con_saldo)
    assert saldo >= Decimal("0")