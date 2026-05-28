# ADR 0003 - select_for_update

## Contexto
Dos peticiones al mismo tiempo pueden gastar el mismo saldo.

## Opciones
1. No bloquear.
2. Bloqueo pesimista.

## Decisión
Se eligió `select_for_update`.

## Consecuencias
- Menos riesgo de doble gasto.
- La operación espera si otra está en curso.

## Fecha y autor
2026-05-28 - Alexander Vallejos