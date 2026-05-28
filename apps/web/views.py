from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from apps.betting.models import Bet, Event
from apps.responsible_gaming.services import get_or_create_deposit_limit
from apps.wallet.services import ensure_user_accounts


def home(request):
    events = Event.objects.order_by("start_at")[:6]
    return render(
        request,
        "web/home.html",
        {
            "events": events,
        },
    )


def login_page(request):
    return render(request, "web/login.html")


def register_page(request):
    return render(request, "web/register.html")


@login_required
def wallet_page(request):
    accounts = ensure_user_accounts(request.user)
    limits = get_or_create_deposit_limit(request.user)

    wallet_account = accounts["wallet_usuario"]
    pending_account = accounts["apuestas_pendientes"]
    bonus_account = accounts["bonos"]

    return render(
        request,
        "web/wallet.html",
        {
            "wallet_balance": wallet_account.balance,
            "pending_balance": pending_account.balance,
            "bonus_balance": bonus_account.balance,
            "limits": limits,
        },
    )


@login_required
def profile_page(request):
    return render(request, "web/profile.html")


@login_required
def history_page(request):
    bets = (
        Bet.objects.filter(user=request.user)
        .select_related("event", "odd")
        .order_by("-placed_at")[:20]
    )
    return render(request, "web/history.html", {"bets": bets})


@login_required
def dashboard_page(request):
    if not request.user.is_staff:
        return render(request, "web/not_allowed.html", status=403)

    totals = Bet.objects.aggregate(total_staked=Sum("stake"), total_paid=Sum("payout"))

    total_staked = totals["total_staked"] or Decimal("0.0000")
    total_paid = totals["total_paid"] or Decimal("0.0000")

    context = {
        "total_apostado": total_staked,
        "total_pagado": total_paid,
        "ggr": total_staked - total_paid,
        "cantidad_usuarios": request.user.__class__.objects.count(),
        "cantidad_apuestas": Bet.objects.count(),
        "cantidad_eventos": Event.objects.count(),
    }
    return render(request, "web/dashboard.html", context)