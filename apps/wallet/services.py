from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import IdempotencyKey, LedgerEntry, LedgerTransaction, WalletAccount

User = get_user_model()

DECIMAL_QUANTIZER = Decimal("0.0001")
HOUSE_STARTING_BALANCE = Decimal("1000000.0000")


def _to_decimal(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise ValidationError("Monto inválido.") from exc

    if amount <= 0:
        raise ValidationError("El monto debe ser mayor que cero.")

    return amount.quantize(DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _get_or_create_house_user():
    house_user, created = User.objects.get_or_create(
        username="house",
        defaults={
            "is_staff": False,
            "is_superuser": False,
            "email": "",
        },
    )
    if created:
        house_user.set_unusable_password()
        house_user.save(update_fields=["password"])
    return house_user


def ensure_user_accounts(user):
    wallet_account, _ = WalletAccount.objects.get_or_create(
        user=user,
        account_type=WalletAccount.AccountType.WALLET_USUARIO,
    )
    pending_account, _ = WalletAccount.objects.get_or_create(
        user=user,
        account_type=WalletAccount.AccountType.APUESTAS_PENDIENTES,
    )
    bonus_account, _ = WalletAccount.objects.get_or_create(
        user=user,
        account_type=WalletAccount.AccountType.BONOS,
    )
    return {
        WalletAccount.AccountType.WALLET_USUARIO: wallet_account,
        WalletAccount.AccountType.APUESTAS_PENDIENTES: pending_account,
        WalletAccount.AccountType.BONOS: bonus_account,
    }


def ensure_house_account():
    house_user = _get_or_create_house_user()
    house_account, _ = WalletAccount.objects.get_or_create(
        user=house_user,
        account_type=WalletAccount.AccountType.CASA,
    )

    if not house_account.entries.exists():
        opening_tx = LedgerTransaction.objects.create(description="Opening house balance")
        LedgerEntry.objects.create(
            transaction=opening_tx,
            account=house_account,
            amount=HOUSE_STARTING_BALANCE,
            direction=LedgerEntry.Direction.CREDIT,
        )

    return house_account


def get_account_balance(account: WalletAccount) -> Decimal:
    return account.balance


def get_user_wallet_account(user):
    accounts = ensure_user_accounts(user)
    return accounts[WalletAccount.AccountType.WALLET_USUARIO]


def _lock_accounts(*accounts):
    account_ids = sorted(account.id for account in accounts)
    locked_accounts = WalletAccount.objects.select_for_update().filter(id__in=account_ids)
    locked_map = {account.id: account for account in locked_accounts}
    return [locked_map[account.id] for account in accounts]


def transfer_between_accounts(
    from_account: WalletAccount,
    to_account: WalletAccount,
    amount,
    idempotency_key: str,
    description: str,
):
    amount = _to_decimal(amount)

    if from_account.id == to_account.id:
        raise ValidationError("La cuenta de origen y destino no pueden ser la misma.")

    with transaction.atomic():
        idem, created = IdempotencyKey.objects.get_or_create(key=idempotency_key)

        if not created and idem.transaction_id:
            return idem.transaction

        from_locked, to_locked = _lock_accounts(from_account, to_account)

        if from_locked.balance < amount:
            raise ValidationError("Saldo insuficiente.")

        tx = LedgerTransaction.objects.create(description=description)

        LedgerEntry.objects.create(
            transaction=tx,
            account=from_locked,
            amount=amount,
            direction=LedgerEntry.Direction.DEBIT,
        )
        LedgerEntry.objects.create(
            transaction=tx,
            account=to_locked,
            amount=amount,
            direction=LedgerEntry.Direction.CREDIT,
        )

        idem.transaction = tx
        idem.save(update_fields=["transaction"])

        return tx


def deposit_virtual_chips(user, amount, idempotency_key: str):
    house_account = ensure_house_account()
    user_wallet = get_user_wallet_account(user)

    return transfer_between_accounts(
        from_account=house_account,
        to_account=user_wallet,
        amount=amount,
        idempotency_key=idempotency_key,
        description="Deposit virtual chips",
    )


def withdraw_virtual_chips(user, amount, idempotency_key: str):
    house_account = ensure_house_account()
    user_wallet = get_user_wallet_account(user)

    return transfer_between_accounts(
        from_account=user_wallet,
        to_account=house_account,
        amount=amount,
        idempotency_key=idempotency_key,
        description="Withdraw virtual chips",
    )