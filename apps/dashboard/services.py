from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum

from apps.betting.models import Bet, Event

Usuario = get_user_model()


def obtener_metricas():
    total_apostado = Bet.objects.aggregate(total=Sum("stake"))["total"] or Decimal("0.0000")
    total_pagado = Bet.objects.aggregate(total=Sum("payout"))["total"] or Decimal("0.0000")

    return {
        "total_apostado": total_apostado,
        "total_pagado": total_pagado,
        "ggr": total_apostado - total_pagado,
        "volumen_apuestas": Bet.objects.count(),
        "usuarios_activos": Usuario.objects.filter(bets__isnull=False).distinct().count(),
        "usuarios_registrados": Usuario.objects.count(),
    }


def obtener_exposicion_eventos():
    eventos = (
        Event.objects.filter(status__in=[Event.Status.PROGRAMADO, Event.Status.EN_VIVO])
        .prefetch_related("odds")
        .order_by("start_at")
    )

    filas = []

    for evento in eventos:
        exposicion = Decimal("0.0000")

        apuestas_aceptadas = Bet.objects.filter(
            event=evento,
            status=Bet.Status.ACCEPTED,
        ).select_related("odd")

        for apuesta in apuestas_aceptadas:
            exposicion += apuesta.stake * (apuesta.odds_snapshot - Decimal("1.0000"))

        filas.append(
            {
                "evento": evento,
                "exposicion": exposicion,
            }
        )

    return filas