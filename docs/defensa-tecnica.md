# Defensa tecnica - FairBet Lab

Este documento resume decisiones simples y defendibles para explicar el proyecto.

## Arquitectura Django

- `apps/users`: registro, perfil y KYC simulado.
- `apps/wallet`: cuentas, ledger y partida doble.
- `apps/betting`: eventos, cuotas, apuestas, liquidacion, combinadas y cash-out.
- `apps/responsible_gaming`: limites de deposito y autoexclusion.
- `apps/audit`: auditoria append-only con hashes encadenados.
- `apps/dashboard`: metricas del operador y reporte CSV.
- `apps/web`: pantallas HTML del MVP.
- `config`: settings, rutas, ASGI, Celery y Channels.

## Reglas de apuesta simples

1. Solo se aceptan apuestas antes de que empiece el evento.
2. Si `event.start_at <= timezone.now()`, el backend rechaza la apuesta.
3. La cuota debe estar activa (`Odd.is_active=True`).
4. El usuario debe estar verificado y no autoexcluido.
5. El monto debe estar entre `MIN_STAKE` y `MAX_STAKE`.
6. El saldo se descuenta con partida doble: wallet del usuario -> apuestas pendientes.
7. La apuesta guarda `odds_snapshot`, que es la cuota aceptada al confirmar.

## KYC simulado

Las cuentas nuevas quedan como `pendiente_verificacion`.

Para la demo existe una verificacion simulada en la pantalla de perfil. El backend valida que el perfil tenga DNI y que la fecha de nacimiento sea mayor de edad. Si pasa, cambia el estado a `verificado`.

Esto mantiene la regla de negocio del reto sin depender de un servicio externo real.

## Cambio de cuota

La pantalla envia la cuota vista por el usuario en `odds_snapshot`.

Antes de registrar la apuesta, el backend compara:

- cuota vista por el usuario
- cuota actual en base de datos

Si son distintas, no registra la apuesta y pide reconfirmar. Asi se evita pagar una cuota vieja si el operador ya la cambio.

## Proteccion de la casa

El evento tiene limites configurables:

- `max_total_bets`: maximo de apuestas aceptadas en el evento.
- `max_bets_per_user`: maximo de apuestas por usuario en el evento.
- `max_event_exposure`: riesgo maximo total de la casa para ese evento.

La cuota tiene:

- `max_selection_exposure`: riesgo maximo por seleccion.

La exposicion se calcula simple:

```text
exposicion = stake * cuota
```

Si una nueva apuesta supera el limite, se rechaza.

## Concurrencia y doble gasto

Las apuestas usan:

- `transaction.atomic()`
- `select_for_update()` sobre cuota y evento
- wallet con movimientos balanceados
- `idempotency_key`

Eso evita que dos apuestas simultaneas descuenten el mismo saldo o creen duplicados por reintentos.

## Si el usuario pierde conexion

Cada apuesta tiene `idempotency_key`.

Si el usuario reintenta la misma operacion, el backend devuelve la apuesta existente en lugar de crear otra. Esto protege contra doble click, refresh o perdida momentanea de conexion.

## Tickets

Cada apuesta funciona como ticket.

Se muestra como:

```text
FB-000001
```

El ticket guarda usuario, evento, seleccion, monto, cuota snapshot, estado, fecha, `transaction_id` e `idempotency_key`.

## Por que no usamos algo mas complejo

Para el MVP se eligio una regla conservadora: al iniciar el evento, se bloquean apuestas nuevas.

Esto es facil de auditar, evita casos ambiguos de apuestas en vivo y reduce riesgo. En una version avanzada se podria permitir in-play con suspension temporal de mercados y reconfirmacion por WebSocket.

## Celery y WebSocket

- Celery queda preparado para tareas de fondo como reportes, cierres programados o activacion de limites despues de 24 horas.
- WebSocket/Channels queda preparado para cuotas en vivo.
- La logica critica no depende de JavaScript ni de Celery: se valida siempre en el backend.
