from apps.wallet.services import get_user_wallet_account


def saldo_navbar(request):
    if not request.user.is_authenticated:
        return {}
    try:
        cuenta_wallet = get_user_wallet_account(request.user)
        return {"navbar_balance": cuenta_wallet.balance}
    except Exception:
        return {"navbar_balance": None}