import uuid
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.betting.models import Bet, Event, Odd
from apps.betting.services import place_simple_bet
from apps.responsible_gaming.models import DepositLimit, SelfExclusion
from apps.responsible_gaming.services import (
    get_or_create_deposit_limit,
    lower_limits,
    request_limit_increase,
    self_exclude,
)
from apps.users.models import UserProfile
from apps.wallet.models import LedgerEntry
from apps.wallet.services import (
    deposit_virtual_chips,
    get_user_wallet_account,
    ensure_user_accounts,
    withdraw_virtual_chips,
)


def _decimal_desde_post(valor):
    try:
        return Decimal(valor).quantize(Decimal("0.0001"))
    except (InvalidOperation, TypeError):
        raise ValueError("Monto invalido.")


def home(request):
    eventos_en_vivo = (
        Event.objects.filter(status=Event.Status.EN_VIVO)
        .prefetch_related("odds")
        .order_by("-start_at")
    )
    eventos_programados = (
        Event.objects.filter(status=Event.Status.PROGRAMADO)
        .prefetch_related("odds")
        .order_by("start_at")
    )
    return render(
        request,
        "betting/home.html",
        {
            "eventos_en_vivo": eventos_en_vivo,
            "eventos_programados": eventos_programados,
        },
    )


def login_view(request):
    if request.method == "POST":
        correo = (request.POST.get("email") or "").strip()
        contrasena = request.POST.get("password") or ""
        usuario = authenticate(request, username=correo, password=contrasena)
        if usuario:
            login(request, usuario)
            return redirect("web-home")
        messages.error(request, "Credenciales invalidas.")
    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    return redirect("web-home")


def register_view(request):
    if request.method == "POST":
        correo = (request.POST.get("email") or "").strip()
        dni = (request.POST.get("dni") or "").strip()
        fecha_nacimiento = request.POST.get("birth_date")
        nombres = (request.POST.get("first_name") or "").strip()
        apellidos = (request.POST.get("last_name") or "").strip()
        contrasena = request.POST.get("password") or ""

        errores = []

        if not correo:
            errores.append("El correo es obligatorio.")
        if not dni:
            errores.append("El DNI es obligatorio.")
        if not fecha_nacimiento:
            errores.append("La fecha de nacimiento es obligatoria.")
        if not nombres:
            errores.append("El nombre es obligatorio.")
        if not apellidos:
            errores.append("El apellido es obligatorio.")
        if not contrasena:
            errores.append("La contraseña es obligatoria.")

        if errores:
            return render(
                request,
                "auth/register.html",
                {"errors": errores, "form": request.POST},
            )

        try:
            fecha_nacimiento = timezone.datetime.fromisoformat(fecha_nacimiento).date()
        except Exception:
            return render(
                request,
                "auth/register.html",
                {"errors": ["La fecha de nacimiento no es valida."], "form": request.POST},
            )

        if UserProfile.objects.filter(document_number=dni).exists():
            return render(
                request,
                "auth/register.html",
                {"errors": ["Ese DNI ya esta registrado."], "form": request.POST},
            )

        if UserProfile.objects.filter(user__username=correo).exists():
            return render(
                request,
                "auth/register.html",
                {"errors": ["Ese correo ya esta registrado."], "form": request.POST},
            )

        if not fecha_nacimiento:
            return render(
                request,
                "auth/register.html",
                {"errors": ["La fecha de nacimiento no es valida."], "form": request.POST},
            )

        usuario = UserProfile._meta.get_field("user").related_model.objects.create_user(
            username=correo,
            email=correo,
            password=contrasena,
            first_name=nombres,
            last_name=apellidos,
        )

        UserProfile.objects.create(
            user=usuario,
            dni=dni,
            birth_date=fecha_nacimiento,
            kyc_status=UserProfile.KYCStatus.PENDING,
        )

        messages.success(request, "Cuenta creada correctamente.")
        return redirect("web-login")

    return render(request, "auth/register.html")


@login_required(login_url="web-login")
def bet_view(request, seleccion_id):
    seleccion = get_object_or_404(Odd.objects.select_related("event"), pk=seleccion_id)
    saldo = get_user_wallet_account(request.user).balance

    if request.method == "POST":
        perfil = getattr(request.user, "profile", None)
        if not perfil or perfil.kyc_status != UserProfile.KYCStatus.VERIFIED:
            messages.error(request, "Tu cuenta debe estar verificada para apostar.")
            return redirect("web-home")

        evento = seleccion.event

        if evento.status not in [Event.Status.PROGRAMADO, Event.Status.EN_VIVO]:
            messages.error(request, "El evento no está disponible para apuestas.")
            return redirect("web-home")

        if evento.status == Event.Status.PROGRAMADO and evento.start_at <= timezone.now():
            messages.error(request, "El evento ya inició.")
            return redirect("web-home")

        try:
            monto = _decimal_desde_post(request.POST.get("stake"))
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("web-bet", seleccion_id=seleccion.id)

        try:
            apuesta = place_simple_bet(
                user=request.user,
                odd=seleccion,
                stake=monto,
                idempotency_key=f"simple-{request.user.id}-{uuid.uuid4().hex[:12]}",
            )
            messages.success(request, "Apuesta registrada con moneda virtual.")
            return redirect("web-historial")
        except Exception as exc:
            messages.error(request, str(exc))

    return render(
        request,
        "betting/bet.html",
        {"seleccion": seleccion, "saldo": saldo},
    )


@login_required(login_url="web-login")
def wallet_view(request):
    cuenta_wallet = get_user_wallet_account(request.user)

    if request.method == "POST":
        accion = request.POST.get("action")
        try:
            monto = _decimal_desde_post(request.POST.get("amount"))
            if accion == "deposit":
                perfil = getattr(request.user, "profile", None)
                if not perfil or perfil.kyc_status != UserProfile.KYCStatus.VERIFIED:
                    raise ValueError("Tu cuenta debe estar verificada para realizar depositos.")

                mapa_limites = {
                    "deposit_limit_daily": "diario",
                    "deposit_limit_weekly": "semanal",
                    "deposit_limit_monthly": "mensual",
                }
                for campo, etiqueta in mapa_limites.items():
                    limite = getattr(request.user, campo, None)
                    if limite is not None and monto > limite:
                        raise ValueError(f"El monto supera tu limite {etiqueta} de deposito ({limite}).")

                deposit_virtual_chips(
                    request.user,
                    monto,
                    idempotency_key=f"deposit-{request.user.id}-{uuid.uuid4().hex[:12]}",
                )
                messages.success(request, "Deposito virtual realizado correctamente.")

            elif accion == "withdraw":
                withdraw_virtual_chips(
                    request.user,
                    monto,
                    idempotency_key=f"withdraw-{request.user.id}-{uuid.uuid4().hex[:12]}",
                )
                messages.success(request, "Retiro virtual realizado correctamente.")

            return redirect("web-wallet")

        except Exception as exc:
            messages.error(request, str(exc))

    entradas = LedgerEntry.objects.filter(account=cuenta_wallet).order_by("-created_at")[:10]
    return render(
        request,
        "wallet/wallet.html",
        {
            "balance": cuenta_wallet.balance,
            "entries": entradas,
        },
    )


@login_required(login_url="web-login")
def historial_view(request):
    apuestas = Bet.objects.filter(user=request.user).select_related("odd", "event").order_by("-placed_at")
    won_count = apuestas.filter(status=Bet.Status.WON).count()
    lost_count = apuestas.filter(status=Bet.Status.LOST).count()
    pending_count = apuestas.filter(status=Bet.Status.ACCEPTED).count()

    listado = []
    for apuesta in apuestas[:20]:
        payout = None
        if apuesta.status == Bet.Status.WON:
            payout = (apuesta.stake * apuesta.odds_snapshot) - apuesta.stake
        listado.append(
            {
                "id": apuesta.id,
                "event": apuesta.event,
                "odd": apuesta.odd,
                "stake": apuesta.stake,
                "odds": apuesta.odds_snapshot,
                "status": apuesta.status,
                "placed_at": apuesta.placed_at,
                "payout": payout,
            }
        )

    return render(
        request,
        "betting/historial.html",
        {
            "bets": listado,
            "won_count": won_count,
            "lost_count": lost_count,
            "pending_count": pending_count,
        },
    )


@login_required(login_url="web-login")
def dashboard_view(request):
    if not request.user.is_staff:
        return redirect("web-login")

    total_apostado = sum(
        [bet.stake for bet in Bet.objects.all()],
        Decimal("0.0000"),
    )
    total_pagado = sum(
        [bet.payout for bet in Bet.objects.all()],
        Decimal("0.0000"),
    )

    eventos = Event.objects.filter(
        status__in=[Event.Status.PROGRAMADO, Event.Status.EN_VIVO]
    ).prefetch_related("odds")

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "metrics": {
                "ggr": total_apostado - total_pagado,
                "total_bets": Bet.objects.count(),
                "active_users": Bet.objects.values("user").distinct().count(),
            },
            "events": eventos,
        },
    )


@login_required(login_url="web-login")
def perfil_view(request):
    if request.method == "POST":
        accion = request.POST.get("action")

        if accion == "limits":
            campo = request.POST.get("field_name")
            nuevo_valor = request.POST.get("new_value")

            try:
                nuevo_valor = _decimal_desde_post(nuevo_valor)
                limite_actual = get_or_create_deposit_limit(request.user)

                if campo == "deposit_limit_daily":
                    if limite_actual.daily_limit is not None and nuevo_valor < limite_actual.daily_limit:
                        lower_limits(request.user, daily=nuevo_valor)
                    else:
                        request_limit_increase(request.user, daily=nuevo_valor)
                elif campo == "deposit_limit_weekly":
                    if limite_actual.weekly_limit is not None and nuevo_valor < limite_actual.weekly_limit:
                        lower_limits(request.user, weekly=nuevo_valor)
                    else:
                        request_limit_increase(request.user, weekly=nuevo_valor)
                elif campo == "deposit_limit_monthly":
                    if limite_actual.monthly_limit is not None and nuevo_valor < limite_actual.monthly_limit:
                        lower_limits(request.user, monthly=nuevo_valor)
                    else:
                        request_limit_increase(request.user, monthly=nuevo_valor)

                messages.success(request, "Limite actualizado.")
                return redirect("web-perfil")
            except Exception as exc:
                messages.error(request, str(exc))

        elif accion == "self_exclusion":
            if request.POST.get("confirm") != "on":
                messages.error(request, "Debes confirmar explicitamente la autoexclusion.")
            else:
                try:
                    self_exclude(request.user, request.POST.get("exclusion_type"))
                    messages.success(request, "Autoexclusion registrada.")
                    return redirect("web-perfil")
                except Exception as exc:
                    messages.error(request, str(exc))

    return render(
        request,
        "auth/perfil.html",
        {
            "exclusion_types": SelfExclusion.Duration.choices,
            "perfil": getattr(request.user, "profile", None),
            "limite": get_or_create_deposit_limit(request.user),
        },
    )