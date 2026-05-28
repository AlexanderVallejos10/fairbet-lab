from decimal import Decimal
import uuid

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.betting.models import Bet, Event, Odd
from apps.betting.services import place_combined_bet
from apps.responsible_gaming.services import get_or_create_deposit_limit
from apps.users.models import UserProfile
from apps.web.forms import LoginForm, RegisterForm
from apps.wallet.services import ensure_user_accounts

User = get_user_model()


def _build_coupon_data(request):
    raw_coupon = request.session.get("coupon", [])
    coupon_items = []
    needs_reconfirm = False
    total_odds = Decimal("1.0000")

    for item in raw_coupon:
        odd = Odd.objects.select_related("event").filter(pk=item.get("odd_id")).first()
        if not odd:
            continue

        stored_odds = Decimal(str(item.get("odds", "1.0000")))
        current_odds = odd.decimal_odds
        changed = stored_odds != current_odds

        if changed:
            needs_reconfirm = True

        coupon_items.append(
            {
                "odd_id": odd.id,
                "home_team": odd.event.home_team,
                "away_team": odd.event.away_team,
                "selection": odd.get_selection_display(),
                "stored_odds": stored_odds,
                "current_odds": current_odds,
                "changed": changed,
            }
        )
        total_odds *= current_odds

    total_odds = total_odds.quantize(Decimal("0.0001"))
    request.session["coupon_requires_reconfirm"] = needs_reconfirm
    request.session.modified = True

    return coupon_items, total_odds, needs_reconfirm


def home(request):
    events = Event.objects.prefetch_related("odds").order_by("start_at")[:6]
    return render(request, "web/home.html", {"events": events})


def events_page(request):
    events = Event.objects.prefetch_related("odds").order_by("start_at")
    coupon_items, coupon_total_odds, coupon_requires_reconfirm = _build_coupon_data(request)

    return render(
        request,
        "web/events.html",
        {
            "events": events,
            "coupon_items": coupon_items,
            "coupon_total_odds": coupon_total_odds,
            "coupon_requires_reconfirm": coupon_requires_reconfirm,
        },
    )


def login_page(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/")
    else:
        form = LoginForm(request)

    return render(request, "web/login.html", {"form": form})


def register_page(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data.get("email", ""),
                    password=form.cleaned_data["password1"],
                )
                UserProfile.objects.create(
                    user=user,
                    document_type=form.cleaned_data["document_type"],
                    document_number=form.cleaned_data["document_number"],
                    birth_date=form.cleaned_data["birth_date"],
                    kyc_status=UserProfile.KYCStatus.PENDING,
                )

            messages.success(request, "Registro creado. Ya puedes iniciar sesión.")
            return redirect("web:login")
    else:
        form = RegisterForm()

    return render(request, "web/register.html", {"form": form})


@login_required
def wallet_page(request):
    accounts = ensure_user_accounts(request.user)
    limits = get_or_create_deposit_limit(request.user)

    return render(
        request,
        "web/wallet.html",
        {
            "wallet_balance": accounts["wallet_usuario"].balance,
            "pending_balance": accounts["apuestas_pendientes"].balance,
            "bonus_balance": accounts["bonos"].balance,
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
        return HttpResponseForbidden("No autorizado.")

    totals = Bet.objects.aggregate(total_staked=Sum("stake"), total_paid=Sum("payout"))
    total_staked = totals["total_staked"] or Decimal("0.0000")
    total_paid = totals["total_paid"] or Decimal("0.0000")

    context = {
        "total_apostado": total_staked,
        "total_pagado": total_paid,
        "ggr": total_staked - total_paid,
        "cantidad_usuarios": User.objects.count(),
        "cantidad_apuestas": Bet.objects.count(),
        "cantidad_eventos": Event.objects.count(),
    }
    return render(request, "web/dashboard.html", context)


def add_to_coupon(request, odd_id):
    odd = get_object_or_404(Odd, pk=odd_id)
    coupon = request.session.get("coupon", [])

    if any(item.get("odd_id") == odd.id for item in coupon):
        messages.info(request, "Esa selección ya está en el cupón.")
        return redirect("web:events")

    coupon.append(
        {
            "odd_id": odd.id,
            "home_team": odd.event.home_team,
            "away_team": odd.event.away_team,
            "selection": odd.get_selection_display(),
            "odds": str(odd.decimal_odds),
        }
    )

    request.session["coupon"] = coupon
    request.session["coupon_requires_reconfirm"] = False
    request.session.modified = True

    return redirect("web:events")


def sync_coupon(request):
    if request.method != "POST":
        return redirect("web:events")

    raw_coupon = request.session.get("coupon", [])
    refreshed = []

    for item in raw_coupon:
        odd = Odd.objects.select_related("event").filter(pk=item.get("odd_id")).first()
        if not odd:
            continue

        refreshed.append(
            {
                "odd_id": odd.id,
                "home_team": odd.event.home_team,
                "away_team": odd.event.away_team,
                "selection": odd.get_selection_display(),
                "odds": str(odd.decimal_odds),
            }
        )

    request.session["coupon"] = refreshed
    request.session["coupon_requires_reconfirm"] = False
    request.session.modified = True

    messages.success(request, "Cupón actualizado con las nuevas cuotas.")
    return redirect("web:events")


def clear_coupon(request):
    request.session["coupon"] = []
    request.session["coupon_requires_reconfirm"] = False
    request.session.modified = True
    return redirect("web:events")


@login_required
def place_coupon_bet(request):
    if request.method != "POST":
        return redirect("web:events")

    if request.session.get("coupon_requires_reconfirm"):
        messages.error(request, "Las cuotas cambiaron. Actualiza el cupón antes de apostar.")
        return redirect("web:events")

    coupon = request.session.get("coupon", [])
    if len(coupon) < 2:
        messages.error(request, "El cupón necesita al menos 2 selecciones.")
        return redirect("web:events")

    odd_ids = [item["odd_id"] for item in coupon]
    stake = request.POST.get("stake", "").strip()

    if not stake:
        messages.error(request, "Debes indicar un monto.")
        return redirect("web:events")

    try:
        combined_bet = place_combined_bet(
            user=request.user,
            odd_ids=odd_ids,
            stake=stake,
            idempotency_key=f"coupon-{request.user.id}-{uuid.uuid4().hex[:12]}",
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return redirect("web:events")

    request.session["coupon"] = []
    request.session["coupon_requires_reconfirm"] = False
    request.session.modified = True

    messages.success(request, f"Combinada creada: cuota {combined_bet.odds_snapshot}")
    return redirect("web:historial")