# FairBet Lab

Plataforma educativa de apuestas deportivas con moneda virtual.  
No maneja dinero real ni integra pasarelas de pago.

## Stack

- Django 5.x
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Django Channels
- Docker Compose

## Qué hace el proyecto

- Registro de usuario con DNI peruano y mayoría de edad.
- Wallet con partida doble.
- Eventos deportivos con cuotas 1X2.
- Apuestas simples.
- Juego responsable con límites y autoexclusión.
- Auditoría encadenada por hashes.
- Dashboard básico del operador.

## Aviso importante

Plataforma educativa con moneda virtual. No constituye una casa de apuestas.

## Cómo correrlo

### 1. Crear y activar el entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate.bat