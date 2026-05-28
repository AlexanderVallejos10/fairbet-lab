# ADR 0004 - Idempotency key

## Contexto
Una misma petición puede llegar dos veces.

## Opciones
1. Confiar en el cliente.
2. Guardar una clave única por operación.

## Decisión
Se eligió usar idempotency key.

## Consecuencias
- No se duplica un depósito o una apuesta.
- La operación se puede repetir sin romper nada.

## Fecha y autor
2026-05-28 - Alexander Vallejos