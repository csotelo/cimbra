# Ximbra

Sistema inteligente de detección y alerta temprana de tormentas eléctricas.
Red neuronal predictiva + alertas multi-canal (web, Telegram, móvil Android).

## Stack

```
ximbra/
├── backend/      Django 5 + DRF + Celery + Django Channels
├── frontend/     Vue 3 + Vite + TailwindCSS
├── apiauth/      FastAPI — token validation + rate limiting (read-only, internal only)
└── watchdog/     Python service — Redis Streams consumer + command executor
```

## Levantar el stack

```bash
cp .env.example .env   # configurar variables
docker compose up --build
```

Acceder en http://localhost:3000 — admin por defecto: `admin@ximbra.local` / `P4ssw0rd!`

> Cambiar credenciales inmediatamente. El admin se crea en la migración inicial solo si no existe ningún superusuario.

## Entornos

| Archivo | Uso |
|---|---|
| `docker-compose.yml` | Desarrollo (uvicorn hot-reload + Vite dev server) |
| `docker-compose.prod.yml` | Producción (gunicorn + nginx) |

## Variables clave

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Requerida |
| `FASTAPI_SECRET_KEY` | Clave compartida para JWT de API tokens |
| `POSTGRES_*` | Conexión a base de datos |
| `REDIS_URL` | Redis (broker + channel layer + result backend) |
| `SINGLE_TENANT_MODE` | `True` para modo uni-tenant (default) |
| `MAIN_TENANT_SLUG` | Slug del tenant principal (default: `ximbra`) |
| `DEFAULT_ADMIN_EMAIL` | Email del superusuario inicial |
| `DEFAULT_ADMIN_PASSWORD` | Contraseña del superusuario inicial |

## Restricciones de acceso

- **DRF (Django REST Framework)**: acceso **solo interno** vía red Docker. No expuesto al host.
- **FastAPI apiauth**: acceso interno para validación de tokens y rate limiting.
- **Frontend Vue**: único punto de entrada público (puerto 3000).

## Licencia

MIT
