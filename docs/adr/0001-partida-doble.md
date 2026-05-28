# ADR 0001 - Partida doble

## Contexto
La wallet necesita registrar cada movimiento de forma clara.

## Opciones
1. Guardar saldo en una columna.
2. Calcular saldo desde movimientos.

## Decisión
Se eligió calcular saldo desde movimientos.

## Consecuencias
- Más trazabilidad.
- Menos riesgo de inconsistencia.
- El saldo depende del historial.

## Fecha y autor
2026-05-28 - Alexander Vallejos