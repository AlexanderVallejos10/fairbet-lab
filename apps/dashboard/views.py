import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render

from .services import obtener_exposicion_eventos, obtener_metricas


@staff_member_required
def panel_dashboard(request):
    contexto = obtener_metricas()
    contexto["eventos_expuestos"] = obtener_exposicion_eventos()
    return render(request, "dashboard/dashboard.html", contexto)


@staff_member_required
def reporte_mensual_csv(request):
    respuesta = HttpResponse(content_type="text/csv")
    respuesta["Content-Disposition"] = 'attachment; filename="reporte_mensual_fairbet.csv"'

    escritor = csv.writer(respuesta)
    escritor.writerow(["metric", "value"])

    metricas = obtener_metricas()
    escritor.writerow(["total_apostado", metricas["total_apostado"]])
    escritor.writerow(["total_pagado", metricas["total_pagado"]])
    escritor.writerow(["ggr", metricas["ggr"]])
    escritor.writerow(["volumen_apuestas", metricas["volumen_apuestas"]])
    escritor.writerow(["usuarios_activos", metricas["usuarios_activos"]])
    escritor.writerow(["usuarios_registrados", metricas["usuarios_registrados"]])

    escritor.writerow([])
    escritor.writerow(["evento", "exposicion"])

    for fila in obtener_exposicion_eventos():
        evento = fila["evento"]
        escritor.writerow([
            f"{evento.home_team} vs {evento.away_team}",
            fila["exposicion"],
        ])

    return respuesta