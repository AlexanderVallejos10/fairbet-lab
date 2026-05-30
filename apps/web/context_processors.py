from decimal import Decimal
from apps.wallet.services import get_balance, get_or_create_wallet

def wallet_balance(request):
    if not request.user.is_authenticated:
        return {'wallet_balance': Decimal('0.0000')}

    try:
        get_or_create_wallet(request.user)
        return {'wallet_balance': get_balance(request.user)}
    except Exception:
        return {'wallet_balance': Decimal('0.0000')}