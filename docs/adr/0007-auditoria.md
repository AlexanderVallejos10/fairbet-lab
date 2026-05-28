# ADR 0007 - Auditoría por hash

## Contexto
Se necesita registrar eventos importantes con trazabilidad.

## Opciones
1. Tabla normal.
2. Cadena de hashes.

## Decisión
Se eligió una cadena de hashes.

## Consecuencias
- Se detectan cambios en registros antiguos.
- La verificación es más fuerte.

## Fecha y autor
2026-05-28 - Alexander Vallejos