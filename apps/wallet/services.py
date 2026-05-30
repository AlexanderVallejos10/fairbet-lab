import uuid
from decimal import Decimal

from django.db import transaction

from apps.users.choices import AccountStatus
from apps.wallet.models import Account, AccountType, Direction, LedgerEntry


class SaldoInsuficiente(Exception):
    pass


class CuentaNoEncontrada(Exception):
    pass


def _to_decimal(amount):
    return amount if isinstance(amount, Decimal) else Decimal(str(amount))


def _estado_kyc_usuario(usuario):
    if hasattr(usuario, "account_status"):
        return usuario.account_status
    perfil = getattr(usuario, "perfil", None) or getattr(usuario, "profile", None)
    if perfil:
        return getattr(perfil, "estado_kyc", None) or getattr(perfil, "kyc_status", None)
    return AccountStatus.VERIFICADO


def _get_account(user, account_type):
    try:
        return Account.objects.get(user=user, type=account_type)
    except Account.DoesNotExist:
        raise CuentaNoEncontrada(
            f"No existe cuenta {account_type} para el usuario {getattr(user, 'email', user)}"
        )


def _get_global_account(account_type):
    account, _ = Account.objects.get_or_create(user=None, type=account_type)
    return account


def _calcular_saldo(account):
    entradas = LedgerEntry.objects.filter(account=account)
    creditos = sum(e.amount for e in entradas if e.direction == Direction.CREDIT)
    debitos = sum(e.amount for e in entradas if e.direction == Direction.DEBIT)
    return creditos - debitos


def _lock_account(account):
    return Account.objects.select_for_update().get(pk=account.pk)


def _crear_par_balanceado(cuenta_origen, cuenta_destino, amount, description, transaction_id=None):
    amount = _to_decimal(amount)
    tid = str(transaction_id or uuid.uuid4())
    LedgerEntry.objects.create(
        account=cuenta_origen,
        amount=amount,
        direction=Direction.DEBIT,
        transaction_id=tid,
        description=f"{description} — débito {cuenta_origen.type}",
    )
    LedgerEntry.objects.create(
        account=cuenta_destino,
        amount=amount,
        direction=Direction.CREDIT,
        transaction_id=tid,
        description=f"{description} — crédito {cuenta_destino.type}",
    )
    return tid


def get_or_create_wallet(user):
    account, _ = Account.objects.get_or_create(
        user=user,
        type=AccountType.WALLET_USUARIO,
    )
    return account


def ensure_user_accounts(user):
    wallet = get_or_create_wallet(user)
    pendientes, _ = Account.objects.get_or_create(user=None, type=AccountType.APUESTAS_PENDIENTES)
    bonos, _ = Account.objects.get_or_create(user=None, type=AccountType.BONOS)
    casa, _ = Account.objects.get_or_create(user=None, type=AccountType.CASA)
    return {
        "wallet_usuario": wallet,
        "apuestas_pendientes": pendientes,
        "bonos": bonos,
        "casa": casa,
        AccountType.WALLET_USUARIO: wallet,
        AccountType.APUESTAS_PENDIENTES: pendientes,
        AccountType.BONOS: bonos,
        AccountType.CASA: casa,
    }


def get_user_wallet_account(user):
    return get_or_create_wallet(user)


def ensure_house_account():
    return _get_global_account(AccountType.CASA)


def transfer_between_accounts(from_account, to_account, amount, idempotency_key=None, description=""):
    return _crear_par_balanceado(
        cuenta_origen=from_account,
        cuenta_destino=to_account,
        amount=amount,
        description=description,
        transaction_id=idempotency_key,
    )


def deposit_virtual_chips(user, amount, idempotency_key=None):
    return deposit(user, amount, transaction_id=idempotency_key)


def withdraw_virtual_chips(user, amount, idempotency_key=None):
    return withdraw(user, amount, transaction_id=idempotency_key)


def get_balance(user):
    with transaction.atomic():
        wallet = _get_account(user, AccountType.WALLET_USUARIO)
        _lock_account(wallet)
        return _calcular_saldo(wallet)


def deposit(user, amount, transaction_id=None):
    amount = _to_decimal(amount)
    if amount <= Decimal("0"):
        raise ValueError("El monto debe ser mayor a cero.")

    if transaction_id and LedgerEntry.objects.filter(transaction_id=transaction_id).exists():
        return transaction_id

    with transaction.atomic():
        wallet = get_or_create_wallet(user)
        _lock_account(wallet)
        casa = _get_global_account(AccountType.CASA)
        tid = _crear_par_balanceado(
            cuenta_origen=casa,
            cuenta_destino=wallet,
            amount=amount,
            description="depósito simulado de fichas",
            transaction_id=transaction_id,
        )
    return tid


def withdraw(user, amount, transaction_id=None):
    amount = _to_decimal(amount)
    if amount <= Decimal("0"):
        raise ValueError("El monto debe ser mayor a cero.")

    if _estado_kyc_usuario(user) not in [AccountStatus.VERIFICADO, "verificado"]:
        raise ValueError("Tu cuenta debe estar verificada para realizar retiros.")

    if transaction_id and LedgerEntry.objects.filter(transaction_id=transaction_id).exists():
        return transaction_id

    with transaction.atomic():
        if transaction_id and LedgerEntry.objects.select_for_update().filter(transaction_id=transaction_id).exists():
            return transaction_id

        wallet = _get_account(user, AccountType.WALLET_USUARIO)
        wallet = _lock_account(wallet)
        saldo = _calcular_saldo(wallet)

        if saldo < amount:
            raise SaldoInsuficiente(f"Saldo insuficiente: tiene {saldo}, necesita {amount}.")

        casa = _get_global_account(AccountType.CASA)
        tid = _crear_par_balanceado(
            cuenta_origen=wallet,
            cuenta_destino=casa,
            amount=amount,
            description="retiro virtual de fichas",
            transaction_id=transaction_id,
        )
    return tid


def reserve_for_bet(user, amount, transaction_id=None):
    amount = _to_decimal(amount)
    if amount <= Decimal("0"):
        raise ValueError("El monto debe ser mayor a cero.")

    if transaction_id and LedgerEntry.objects.filter(transaction_id=transaction_id).exists():
        return transaction_id

    with transaction.atomic():
        wallet = _get_account(user, AccountType.WALLET_USUARIO)
        _lock_account(wallet)
        saldo = _calcular_saldo(wallet)

        if saldo < amount:
            raise SaldoInsuficiente(f"Saldo insuficiente: tiene {saldo}, necesita {amount}.")

        pendientes = _get_global_account(AccountType.APUESTAS_PENDIENTES)
        tid = _crear_par_balanceado(
            cuenta_origen=wallet,
            cuenta_destino=pendientes,
            amount=amount,
            description="reserva de fondos para apuesta",
            transaction_id=transaction_id,
        )
    return tid


def settle_win(user, stake, odds, transaction_id=None):
    stake = _to_decimal(stake)
    odds = _to_decimal(odds)
    if transaction_id and LedgerEntry.objects.filter(transaction_id=transaction_id).exists():
        return transaction_id

    payout = (stake * odds).quantize(Decimal("0.0001"))

    with transaction.atomic():
        pendientes = _get_global_account(AccountType.APUESTAS_PENDIENTES)
        wallet = _get_account(user, AccountType.WALLET_USUARIO)
        _lock_account(wallet)
        tid = _crear_par_balanceado(
            cuenta_origen=pendientes,
            cuenta_destino=wallet,
            amount=payout,
            description=f"liquidación ganada — payout {payout} (stake {stake} × odds {odds})",
            transaction_id=transaction_id,
        )
    return tid


def settle_loss(user, stake, transaction_id=None):
    stake = _to_decimal(stake)
    if transaction_id and LedgerEntry.objects.filter(transaction_id=transaction_id).exists():
        return transaction_id

    with transaction.atomic():
        pendientes = _get_global_account(AccountType.APUESTAS_PENDIENTES)
        casa = _get_global_account(AccountType.CASA)
        wallet = _get_account(user, AccountType.WALLET_USUARIO)
        _lock_account(wallet)
        tid = _crear_par_balanceado(
            cuenta_origen=pendientes,
            cuenta_destino=casa,
            amount=stake,
            description=f"liquidación perdida — stake {stake} a la casa",
            transaction_id=transaction_id,
        )
    return tid
