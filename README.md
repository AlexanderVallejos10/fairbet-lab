# FairBet Lab

Simulador educativo de apuestas deportivas con fichas virtuales. No integra pasarelas de pago, no convierte fichas a dinero real y muestra el aviso obligatorio:

> Plataforma educativa con moneda virtual. No constituye una casa de apuestas.

## Stack

- Django 5.x
- Django REST Framework
- PostgreSQL para Docker
- SQLite para desarrollo local simple
- Redis, Celery y Django Channels
- drf-spectacular para OpenAPI/Swagger
- pytest + pytest-django

## Funcionalidades

- Registro con DNI, fecha de nacimiento y estado KYC simulado.
- Estados de cuenta: pendiente_verificacion, verificado, bloqueado, autoexcluido.
- Wallet con partida doble usando `LedgerEntry`.
- Saldo derivado por creditos menos debitos, sin guardar saldo en base de datos.
- Recarga y retiro simulados de fichas.
- Eventos deportivos con mercado 1X2.
- Apuesta simple, combinada y cash-out por API.
- Validaciones de saldo, KYC, evento, monto minimo/maximo e idempotencia.
- Bloqueo automatico de apuestas cuando el evento ya inicio.
- Reconfirmacion si la cuota cambio entre ver la pantalla y confirmar.
- Limites simples para proteger a la casa: maximo por usuario, maximo por evento y exposicion maxima.
- Juego responsable: limites de deposito y autoexclusion.
- Auditoria append-only con hash encadenado.
- Dashboard de operador y reporte CSV.
- Actualizacion de odds por WebSocket.

## Ejecucion local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abrir:

- Web: http://127.0.0.1:8000/
- Eventos: http://127.0.0.1:8000/events/
- Admin: http://127.0.0.1:8000/admin/
- Swagger: http://127.0.0.1:8000/api/docs/

Usuarios demo:

- Usuario: `demo` / `Demo12345`
- Admin: `admin` / `Admin12345`

## Ejecucion con Docker

```powershell
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

Docker activa PostgreSQL y Redis con estas variables:

```env
USE_POSTGRES=True
USE_REDIS_CHANNELS=True
```

## Tests

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest -q
```

Estado actual validado:

```text
System check identified no issues
33 passed
```

## Reglas simples de negocio

- La cuota aceptada se guarda como `odds_snapshot`.
- Si la cuota cambio antes de confirmar, la apuesta se rechaza y se pide reconfirmar.
- Si el evento ya inicio, el backend bloquea nuevas apuestas.
- Cada evento define `max_total_bets`, `max_bets_per_user` y `max_event_exposure`.
- Cada cuota define `max_selection_exposure`.
- La exposicion se calcula como `stake * cuota`.
- Cada apuesta tiene ticket visible `FB-000001`.
- La logica critica se valida en backend, no en JavaScript.

## Endpoints principales

- `GET /api/betting/events/`
- `POST /api/betting/place/`
- `POST /api/betting/combined/place/`
- `POST /api/betting/events/<id>/settle/`
- `POST /api/betting/bets/<id>/cashout/`
- `GET /api/wallet/balance/`
- `POST /api/wallet/deposit/`
- `POST /api/wallet/withdraw/`
- `GET /api/responsible-gaming/limits/`
- `POST /api/responsible-gaming/limits/`
- `POST /api/responsible-gaming/self-exclusion/`
- `GET /api/audit/verify/`
- `GET /api/dashboard/reporte.csv`

## Documentacion del reto

- ADRs: `docs/adr/`
- Bocetos: `docs/sketches/`
- Compliance: `docs/compliance.md`
- Lecciones: `docs/lecciones.md`
- Declaracion de uso de IA: `docs/anti-ai-disclosure.md`
- Guia de defensa tecnica: `docs/defensa-tecnica.md`
