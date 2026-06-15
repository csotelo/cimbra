# Ximbra — Sistema de Alertas de Tormentas Eléctricas

Sistema de predicción y alerta temprana de tormentas eléctricas para Perú, basado en IA y datos meteorológicos en tiempo real. Combina una plataforma multi-tenant SaaS con un pipeline de Machine Learning de extremo a extremo.

---

## Índice

1. [Visión general](#visión-general)
2. [Arquitectura del sistema](#arquitectura-del-sistema)
3. [Pipeline de datos e IA](#pipeline-de-datos-e-ia)
4. [Stack tecnológico](#stack-tecnológico)
5. [Servicios y contenedores](#servicios-y-contenedores)
6. [Modelos de datos](#modelos-de-datos)
7. [API REST — endpoints](#api-rest--endpoints)
8. [FastAPI — validación y rate limiting](#fastapi--validación-y-rate-limiting)
9. [Frontend](#frontend)
10. [Variables de entorno](#variables-de-entorno)
11. [Despliegue en producción](#despliegue-en-producción)
12. [Configuración de estaciones](#configuración-de-estaciones)

---

## Visión general

Ximbra ingiere variables meteorológicas horarias de la API pública **Open-Meteo**, las procesa con modelos de red neuronal (**MLP / LSTM**) calibrados con Platt Scaling, genera alertas de tormenta según la escala SENAMHI (Verde / Amarillo / Naranja / Rojo) y las distribuye a través de un dashboard web y un bot de Telegram.

La plataforma es multi-tenant con aislamiento lógico: múltiples organizaciones comparten la misma base de datos con separación por software.

```
Open-Meteo API ──► Ingestor ──► PostgreSQL/PostGIS ──► Predictor ──► StormAlerts
                                                              │
                                                        Trainer (ML)
                                                              │
                                                     Django Admin + Vue SPA
                                                              │
                                                       Telegram Bot
```

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CLIENTE (Browser)                                                      │
│  Vue 3 SPA — Tailwind CSS — Pinia — Axios                               │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ HTTP :80
┌───────────────────────────▼─────────────────────────────────────────────┐
│  nginx (vue container)                                                  │
│  /         → static SPA                                                 │
│  /api/*    → proxy_pass http://django:8000                              │
│  /ws/*     → proxy_pass ws://django:8000 (WebSocket)                   │
└─────────┬───────────────────────────────────────────────────────────────┘
          │ red interna ximbra_app_network
          │
┌─────────▼──────────┐    ┌──────────────────┐    ┌──────────────────────┐
│  Django :8000      │    │  FastAPI :8001    │    │  Celery Worker       │
│  DRF + Channels    │    │  Hexagonal arch.  │    │  + Celery Beat       │
│  Admin (Unfold)    │    │  Token validation │    │  Tareas asíncronas   │
│  JWT Auth          │    │  Rate limiting    │    │  Emails, jobs        │
└────────┬───────────┘    └────────┬──────────┘    └──────────────────────┘
         │                         │
┌────────▼─────────────────────────▼────────────────────────────────────┐
│  PostgreSQL + PostGIS :5432   Redis :6379    MongoDB :27017            │
│  Datos relacionales           Cache/Broker   Datos documentales        │
│  Geometrías estaciones        Pub/Sub        (sin AVX, mongo:4.4)      │
│  Observaciones/Alertas        Rate limits                              │
└────────┬──────────────────────────────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────────────────────────────────┐
│  Servicios Python autónomos (ciclos temporales)                          │
│                                                                          │
│  ingestor    → Open-Meteo → WeatherObservation (cada INGESTOR_CYCLE_SEC) │
│  trainer     → PostgreSQL → ModelArtifact .keras + scaler.pkl            │
│  predictor   → modelo activo → StormAlert (cada PREDICTOR_CYCLE_SEC)     │
│  watchdog    → heartbeats Redis → estado de servicios                    │
│  telegram_bot → StormAlert pendientes → Telegram API                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline de datos e IA

### Fuente de datos: Open-Meteo

Variables meteorológicas obtenidas por coordenadas (lat/lon) de cada estación:

| Variable | Descripción | Uso |
|---|---|---|
| `temperature_2m` | Temperatura superficial (°C) | Feature directo |
| `relative_humidity_2m` | Humedad relativa (%) | Feature directo |
| `surface_pressure` | Presión atmosférica (hPa) | Feature directo |
| `cape` | Energía convectiva disponible (J/kg) | Feature crítico |
| `temperature_850/700/500hPa` | Temperatura por niveles de presión | Para K-Index |
| `relative_humidity_850/700hPa` | Humedad por niveles de presión | Para K-Index |

**K-Index** se calcula internamente a partir de niveles de presión:
```
K-Index = (T850 - T500) + Td850 - (T700 - Td700)
Td ≈ T - (100 - RH) / 5   [aproximación Magnus, válida para RH > 50%]
```

- **Tiempo real** (`ingestor`): `api.open-meteo.com/v1/forecast` — últimas 24h + próximas 24h
- **Histórico** (`trainer`): `archive-api.open-meteo.com/v1/archive` — desde 1940 hasta ~5 días atrás

### CRISP-DM — Fases del pipeline ML

```
[1] Business Understanding
    → Alertas alineadas a escala SENAMHI (4 niveles de riesgo)
    → Predicción binaria: ¿hay riesgo de tormenta en la próxima hora?

[2] Data Understanding
    → Datos históricos 2024-2025 de Open-Meteo Archive por cada estación
    → 5 features físicamente interpretables

[3] Data Preparation  (trainer/app/application/prepare.py)
    → Limpieza de outliers por rango físico:
        temperature  (-20, 50°C)
        humidity     (0, 100%)
        pressure     (500, 1100 hPa)
        cape         (0, 10000 J/kg)
        k_index      (-20, 60)
    → Label binario heurístico SENAMHI-aligned:
        CAPE ≥ 500 J/kg  AND  K-Index ≥ 20  →  storm = 1
    → Normalización Min-Max (sklearn MinMaxScaler, persistido como scaler.pkl)
    → Split 70 / 15 / 15 (train / val / test)

[4] Modeling  (trainer/app/application/train.py)
    → Arquitectura MLP:
        Input(5) → Dense(64,relu) → Dropout(0.2) → Dense(32,relu)
                 → Dropout(0.2) → Dense(16,relu) → Dense(1,sigmoid)
    → Arquitectura LSTM:
        Input(seq_len=6, 5) → LSTM(64) → Dropout(0.2) → Dense(32,relu)
                            → Dropout(0.2) → Dense(1,sigmoid)
    → Optimizador: Adam lr=0.001
    → Loss: binary_crossentropy
    → EarlyStopping patience=8, max 50 épocas, batch=64
    → Benchmark MLP vs LSTM por ROC-AUC → mejor arquitectura gana

[5] Evaluation  (trainer/app/application/benchmark.py + calibrate.py)
    → Cross-validation por folds (ModelBenchmark)
    → Calibración de probabilidades: Platt Scaling (CalibratedClassifierCV)
    → SHAP DeepExplainer: background set para explicabilidad per-predicción
    → Umbrales calibrados por Youden's J statistic (maximiza Sens + Spec)
    → Métricas: Accuracy, Precision, Recall, F1, ROC-AUC
    → Persistencia: modelo .keras, scaler.pkl, calibrator.pkl, shap_background.npy

[6] Deployment  (predictor/app/application/predict.py — ciclo horario)
    → Carga ModelArtifact con is_active=True desde PostgreSQL
    → Soporta MLP (última observación) y LSTM (últimas 6 observaciones)
    → raw_prob = model.predict(X_scaled)
    → prob_calibrada = calibrador.predict_proba([[raw_prob]])
    → nivel = thresholds_calibrados_youden (verde/amarillo/naranja/rojo)
    → explanation_json = SHAP values por feature (temperatura, humedad, etc.)
    → INSERT StormAlert para cada estación activa
```

### Escala de alertas SENAMHI

| Nivel | Color | Umbral prob. (default) | Significado |
|---|---|---|---|
| 1 | 🟢 Verde | < 0.30 | Sin riesgo |
| 2 | 🟡 Amarillo | 0.30 – 0.60 | Riesgo moderado |
| 3 | 🟠 Naranja | 0.60 – 0.85 | Peligroso |
| 4 | 🔴 Rojo | ≥ 0.85 | Riesgo extremo |

Los umbrales se ajustan automáticamente por Youden's J tras la calibración y se persisten en `ModelArtifact.thresholds_json`.

### Flujo de notificación

```
StormAlert generado por predictor
       │
       ├─► Django API /api/weather/alerts/
       │        └─► Vue SPA — mapa Leaflet con colores por nivel
       │
       └─► telegram_bot (ciclo cada TELEGRAM_NOTIFIER_CYCLE_SEC)
               │
               ├─ Consulta alertas sin telegram_notified_at
               ├─ Filtra TelegramSubscription por department + min_level
               ├─ Envía mensaje Markdown vía python-telegram-bot
               │     ⚡ ALERTA TORMENTA — Nivel X — Estación — prob% — SHAP
               └─ Marca telegram_notified_at en PostgreSQL
```

---

## Stack tecnológico

### Backend

| Tecnología | Versión | Rol |
|---|---|---|
| Python | 3.12 | Runtime |
| Django | 5.1.4 | API REST, Admin, WebSockets, ORM |
| Django REST Framework | 3.15.2 | Serializers, ViewSets, permisos |
| Django Unfold | 0.34.0 | Admin moderno |
| djangorestframework-simplejwt | 5.5.0 | JWT (access + refresh + blacklist) |
| Django Channels | 4.2.0 | WebSockets |
| GeoDjango + PostGIS | — | Estaciones con coordenadas geoespaciales |
| Celery | 5.4.0 | Tareas async (emails, jobs) |
| django-celery-beat | 2.7.0 | Scheduler tareas periódicas |
| django-split-settings | — | Settings modulares (base/dev/prod/testing) |
| FastAPI | 0.115.6 | Validación tokens + rate limiting |
| uvicorn | — | ASGI para Django async y FastAPI |
| gunicorn + UvicornWorker | — | Servidor producción Django |

### Machine Learning

| Tecnología | Versión | Rol |
|---|---|---|
| TensorFlow / Keras | 2.17.0 | Modelos MLP y LSTM |
| scikit-learn | 1.5.2 | MinMaxScaler, Platt Scaling, métricas |
| XGBoost | 2.0.3 | Modelo alternativo para benchmark |
| SHAP | 0.46.0 | Explicabilidad DeepExplainer por predicción |
| pandas | 2.2.3 | Preparación del dataset |
| numpy | 1.26.4 | Arrays y operaciones numéricas |
| joblib | 1.4.2 | Persistencia scaler, calibrador, SHAP background |
| httpx | 0.27.2 | Cliente HTTP async para Open-Meteo |

### Frontend

| Tecnología | Versión | Rol |
|---|---|---|
| Vue.js | 3.5.13 | SPA, Composition API |
| Pinia | 2.3.0 | Estado global (auth, tenant, config) |
| Vue Router | — | Guards de autenticación, rutas protegidas |
| TailwindCSS | 3.4.17 | Estilos utility-first |
| Axios | — | HTTP con interceptors JWT (refresh automático) |
| Leaflet | — | Mapa interactivo de estaciones y alertas |

### Infraestructura

| Servicio | Imagen | Puerto |
|---|---|---|
| PostgreSQL + PostGIS | `postgis/postgis:16-3.4` | 5432 |
| Redis | `redis:7-alpine` | 6379 |
| MongoDB | `mongo:4.4` | 27017 |
| MinIO | `minio/minio:latest` | 9000 (S3), 9001 (console) |
| nginx | `nginx:alpine` (build) | **80** (público) |
| Django | Python 3.12 (build) | interno |
| FastAPI | Python 3.12 (build) | 8001 (interno) |

---

## Servicios y contenedores

```
ximbra_app_network (bridge Docker)
│
├── vue           nginx — SPA compilada, proxy /api/ → django:8000
├── django        gunicorn + UvicornWorker ASGI, puerto interno 8000
├── celery_worker procesador de tareas async (emails, jobs personalizados)
├── celery_beat   scheduler de tareas periódicas (django-celery-beat)
├── apiauth       FastAPI — validación de API tokens y rate limiting
├── postgres      PostgreSQL + PostGIS — datos relacionales y geoespaciales
├── redis         broker Celery, caché, pub/sub, heartbeats del watchdog
├── mongodb       datos documentales (sin restricción AVX, mongo:4.4)
├── minio         object storage S3-compatible (media, artefactos ML)
├── minio_init    one-shot: crea bucket al primer arranque
│
├── ingestor      ciclo horario — descarga observaciones Open-Meteo → PostgreSQL
├── predictor     ciclo horario — genera StormAlerts con el modelo activo
├── trainer       one-shot bajo demanda — entrena MLP/LSTM, guarda artefactos
├── watchdog      ciclo continuo — procesa heartbeats Redis → estado servicios
└── telegram_bot  ciclo 5min — envía alertas pendientes a suscriptores Telegram
```

### Ciclos temporales configurables

| Servicio | Variable de entorno | Default |
|---|---|---|
| ingestor | `INGESTOR_CYCLE_SEC` | 3600 (1h) |
| predictor | `PREDICTOR_CYCLE_SEC` | 3600 (1h) |
| telegram_bot | `TELEGRAM_NOTIFIER_CYCLE_SEC` | 300 (5 min) |

---

## Modelos de datos

### Multi-tenancy y autenticación

```
CustomUser (email como identificador único)
    │
    └──[M2M via UserTenantRole]──► Tenant
                                      │
                                      └──► APIToken (1 activo por tenant/owner)

Roles: OWNER · ADMIN · MEMBER · SuperAdmin (is_superuser)

Invitation (UUID token, 72h expiración)
Plan / UserSubscription (planes de uso)
Notification (per-user, cross-tenant)
```

#### CustomUser
| Campo | Tipo | Descripción |
|---|---|---|
| `email` | EmailField unique | Identificador (no username) |
| `is_email_verified` | Boolean | Verificación requerida para operar |
| `email_verification_token` | CharField(64) | Token de verificación |
| `password_reset_token` | CharField(64) | Token para reset |
| `is_active / is_staff / is_superuser` | Boolean | Control de acceso |

#### Tenant
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | PK |
| `name / slug` | CharField | Slug auto-generado con unicidad garantizada |
| `is_active` | Boolean | Habilitar/deshabilitar tenant |
| `max_users` | PositiveInt | Límite de miembros (default 10) |
| `rate_limit` | PositiveInt | Requests/minuto para API tokens |

#### APIToken
| Campo | Tipo | Descripción |
|---|---|---|
| `token` | CharField | Mostrado en texto plano solo al crear |
| `tenant / owner` | FK | Propietario y tenant asociado |
| `expires_at` | DateTime | Expiración configurable |
| `last_used_at` | DateTime | Tracking de último uso |
| `is_active` | Boolean | Máximo 1 activo por tenant/owner |

### Meteorología y ML

```
Station (GeoDjango PointField SRID=4326)
    code · name · department · location(lat,lon) · altitude_m · is_active
    │
    ├──► WeatherObservation (upsert horario desde ingestor)
    │         station · observed_at (unique together)
    │         temperature · humidity · pressure · cape · k_index
    │         source="open-meteo" · raw_data (JSON completo)
    │
    └──► StormAlert (generado por predictor cada hora)
              station · observation · probability (calibrada)
              alert_level (1-4) · is_active
              model_version · explanation_json (SHAP por feature)
              notified_at · telegram_notified_at

TelegramSubscription
    chat_id · username · department (vacío=todos) · min_level · is_active

ModelArtifact (artefacto de cada entrenamiento)
    id (UUID) · version · status (training/ready/failed)
    model_path · scaler_path · calibrator_path · shap_background_path
    best_model_type (mlp/lstm) · epochs_run · training_seconds
    accuracy · precision · recall · f1 · roc_auc · loss
    thresholds_json (umbrales Youden calibrados)
    is_active (solo uno activo a la vez)

ModelBenchmark → FK ModelArtifact
    model_type · cv_fold · accuracy · f1 · roc_auc · training_seconds
```

### Notificaciones y plataforma

```
Notification (per-user, no filtrada por tenant)
    tipos: rate_limit_exceeded · tenant_invitation · member_role_changed
           api_token_expiring · system_alert

Jobs (Celery via django-celery-beat)
    task_id · state · result · tenant · created_at
```

---

## API REST — endpoints

Base: `http://<host>/api/`  (nginx hace proxy a django:8000 internamente)

### Autenticación (`/api/users/`)

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `login/` | JWT login — retorna access + refresh token |
| POST | `register/` | Registro — envía email de verificación via Celery |
| POST | `refresh/` | Renovar access token con refresh token |
| POST | `logout/` | Blacklist del refresh token |
| POST | `verify-email/` | Verificar email con token recibido |
| POST | `forgot-password/` | Solicitar reset de contraseña |
| POST | `reset-password/` | Confirmar nuevo password con token |
| POST | `change-password/` | Cambiar password (autenticado) |
| POST | `select-tenant/` | Activar tenant en sesión JWT |
| GET/PUT | `me/` | Perfil del usuario autenticado |
| POST | `invitations/` | Crear y enviar invitación por email |
| GET | `invitations/list/` | Listar invitaciones del tenant activo |
| GET/POST | `invitations/<token>/` | Validar / aceptar invitación |
| GET | `list/` | Listar usuarios (admin/superadmin) |
| POST | `<pk>/toggle/` | Activar o desactivar usuario |

### Tenants (`/api/tenants/`)

CRUD completo. Acceso filtrado por rol: Owner ve configuración completa, Member ve solo datos.

### API Tokens (`/api/tokens/`)

Generación, rotación y revocación. El token se muestra una sola vez al crear.

### Jobs Celery (`/api/jobs/`)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `` | Listar tareas del tenant activo |
| POST | `dispatch/` | Despachar tarea Celery personalizada |
| GET | `<task_id>/` | Estado y resultado de la tarea |

### Clima y alertas (`/api/weather/`)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `stations/` | Lista de estaciones activas |
| GET | `stations/geojson/` | Estaciones en GeoJSON para Leaflet |
| GET | `observations/` | Observaciones meteorológicas recientes |
| GET | `alerts/` | Alertas activas con probabilidad y nivel |
| GET | `alerts/geojson/` | Alertas en GeoJSON con color SENAMHI |
| GET | `telegram/subscriptions/` | Suscripciones Telegram activas |

### Sistema y plataforma

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health/` | Health check del backend |
| GET | `/api/config/` | Configuración pública (SINGLE_TENANT_MODE, etc.) |
| GET | `/api/config/site/` | Branding y nombre del sitio |
| GET | `/api/plans/me/` | Plan de suscripción activo |
| GET | `/api/plans/usage/` | Uso actual vs. límites del plan |
| GET | `/api/dashboard/` | Widgets del dashboard (rate limit, historial) |
| GET | `/api/watchdog/` | Estado de los servicios vía heartbeats |
| GET/PATCH | `/api/notifications/` | Listar, leer y limpiar notificaciones |

---

## FastAPI — validación y rate limiting

Servicio en puerto **8001** (solo red interna Docker, nunca expuesto al exterior).

### Arquitectura hexagonal

```
HTTP Request
    │
    ├── app/api/routes/
    │       process.py    POST /api/v1/process   — ejecuta y consume rate limit
    │       validate.py   GET  /api/v1/validate  — valida token sin consumir
    │       (health)      GET  /health            — healthcheck
    │
    ├── app/application/
    │       process_request.py  — caso de uso: validar + consumir + procesar
    │       validate_token.py   — caso de uso: validar sin efecto lateral
    │       check_rate_limit.py — lógica sliding window en Redis
    │
    ├── app/domain/
    │       api_token.py · tenant.py · user.py · user_tenant_role.py
    │       (entidades puras, sin dependencias de infraestructura)
    │
    └── app/infrastructure/
            postgres_adapter.py  — lectura PostgreSQL (solo lectura, SQLAlchemy Core)
            redis_adapter.py     — rate limiting con ventana deslizante
```

**Headers aceptados:**
- `Authorization: Bearer <token>`
- `X-Api-Token: <token>`

**Respuesta `/api/v1/validate`:**
```json
{
  "valid": true,
  "tenant_id": "uuid",
  "tenant_name": "Ximbra",
  "user_email": "user@example.com",
  "role": "OWNER",
  "message": "Token válido"
}
```

---

## Frontend

SPA Vue 3 servida por nginx en puerto 80. Las peticiones API van a `/api/` (mismo origen) y nginx las proxea internamente a `django:8000`. No hay CORS cross-port.

### Rutas protegidas (requieren JWT)

| Ruta | Vista | Descripción |
|---|---|---|
| `/dashboard` | Dashboard.vue | Widgets: rate limit, salud de servicios, historial |
| `/profile` | Profile.vue | Perfil del usuario |
| `/tenants` | TenantList.vue | Tenants del usuario con roles |
| `/tenants/:slug` | TenantDetail.vue | Miembros, API token, configuración |
| `/tenants/:slug/settings` | TenantSettings.vue | Edición del tenant |
| `/jobs` | JobList.vue | Visor de tareas Celery |
| `/watchdog` | Watchdog.vue | Estado de servicios en tiempo real |
| `/weather/stations` | Stations.vue | Lista de estaciones con estado |
| `/weather/map` | StationMap.vue | Mapa Leaflet de estaciones |
| `/weather/alerts` | StormAlerts.vue | Alertas activas con mapa y colores SENAMHI |
| `/weather/telegram` | TelegramSubscriptions.vue | Gestión de suscripciones Telegram |
| `/admin/users` | UserManagement.vue | Gestión de usuarios (superadmin) |
| `/admin/settings` | SiteSettings.vue | Configuración del sitio |

### Rutas públicas

| Ruta | Vista |
|---|---|
| `/login` | Login.vue |
| `/register` | Register.vue |
| `/verify-email` | VerifyEmail.vue |
| `/forgot-password` | ForgotPassword.vue |
| `/reset-password` | ResetPassword.vue |
| `/invitations/:token` | AcceptInvitation.vue |

### Stores Pinia

| Store | Responsabilidad |
|---|---|
| `auth` | Login, logout, refresh automático, estado del usuario |
| `tenant` | Tenant activo, CRUD, selección de tenant |
| `config` | Configuración del sistema (SINGLE_TENANT_MODE, branding) |

### Composables clave

| Composable | Responsabilidad |
|---|---|
| `useAuth` | Guards de autenticación en el router |
| `useTenant` | Operaciones sobre el tenant activo |
| `useApiToken` | Generación y revocación de API tokens |
| `useNotifications` | Polling de notificaciones no leídas |
| `useHead` | Metadatos SEO dinámicos por ruta |

### Componentes de widgets (dashboard)

| Componente | Descripción |
|---|---|
| `RateLimitGauge.vue` | Gauge visual de uso del rate limit por tenant |
| `ServiceHealth.vue` | Estado de servicios vía heartbeats del watchdog |
| `UsageHistory.vue` | Historial de peticiones API del tenant |
| `NotificationBell.vue` | Badge con conteo de notificaciones no leídas |
| `ApiTokenWidget.vue` | Generación one-shot del API token (mostrado una vez) |
| `MemberList.vue` | Gestión de miembros con cambio de rol e invitaciones |

---

## Variables de entorno

Copia `.env.example` como `.env` y completa los valores antes de desplegar:

```bash
# ── Django ────────────────────────────────────
DJANGO_ENV=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<genera con get_random_secret_key()>
ALLOWED_HOSTS=<IP o dominio>
FRONTEND_URL=http://<IP o dominio>
CORS_ALLOWED_ORIGINS=http://<IP o dominio>

# ── Modo uni-tenant ───────────────────────────
SINGLE_TENANT_MODE=True          # False para multi-tenant
MAIN_TENANT_SLUG=ximbra

# ── PostgreSQL ────────────────────────────────
POSTGRES_DB=ximbra_db
POSTGRES_USER=ximbra_user
POSTGRES_PASSWORD=<password seguro>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ── Redis ─────────────────────────────────────
REDIS_PASSWORD=<password>
REDIS_URL=redis://:<password>@redis:6379
CELERY_BROKER_URL=redis://:<password>@redis:6379/0
CELERY_RESULT_BACKEND=redis://:<password>@redis:6379/0

# ── MongoDB ───────────────────────────────────
MONGODB_URI=mongodb://mongodb:27017
MONGODB_DB=ximbra_mongo

# ── MinIO (S3 local) ──────────────────────────
MINIO_ROOT_USER=<user>
MINIO_ROOT_PASSWORD=<password>
MINIO_BUCKET=ximbra
AWS_S3_ENDPOINT_URL=http://minio:9000

# ── FastAPI ───────────────────────────────────
FASTAPI_SECRET_KEY=<genera con secrets.token_hex(32)>
FASTAPI_ALGORITHM=HS256

# ── Telegram ──────────────────────────────────
TELEGRAM_BOT_TOKEN=<token de @BotFather>
TELEGRAM_NOTIFIER_CYCLE_SEC=300

# ── Ciclos de servicios ML ────────────────────
INGESTOR_CYCLE_SEC=3600
PREDICTOR_CYCLE_SEC=3600
```

---

## Despliegue en producción

### Requisitos

- Docker Engine + Docker Compose v2
- Servidor Linux (probado en Ubuntu/Debian)
- Puerto 80 accesible públicamente

### Primer despliegue

```bash
# 1. Clonar el repositorio en el servidor
git clone git@github.com:csotelo/cimbra.git /home/admin/ximbra
cd /home/admin/ximbra

# 2. Crear .env con los valores reales
cp .env.example .env
# editar .env

# 3. Construir y levantar todo el stack
docker compose up -d --build

# 4. Migraciones y superusuario inicial
docker compose exec django python manage.py migrate
docker compose exec django python manage.py createsuperuser

# 5. Cargar estaciones meteorológicas
docker compose exec django python manage.py seed_stations

# 6. Primer entrenamiento del modelo ML
docker compose run --rm trainer
```

### Flujo de datos completo en producción

```
[Cada hora — automático]
  ingestor  → Open-Meteo forecast → WeatherObservation (upsert por station+hora)
  predictor → última(s) observación(es) → modelo activo → StormAlert

[Cada 5 minutos — automático]
  telegram_bot → StormAlerts sin telegram_notified_at → suscriptores Telegram

[Bajo demanda — manual vía Django Admin o management command]
  trainer → Open-Meteo Archive (histórico 2024-2025) → ModelArtifact
          → activa modelo → predictor lo carga en próximo ciclo
```

### Endpoints públicos en producción

| Recurso | URL |
|---|---|
| Frontend (SPA) | `http://<IP>/` |
| Django Admin | `http://<IP>/admin/` |
| MinIO Console | `http://<IP>:9001/` |
| FastAPI docs | Solo red interna — `http://apiauth:8001/docs` |

---

## Configuración de estaciones

Las estaciones se registran en Django Admin (`/admin/weather/station/`) o via management command. Cada estación requiere:

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | CharField unique | Código SENAMHI (ej. `HUA001`) |
| `name` | CharField | Nombre de la estación |
| `department` | CharField | Departamento — usado para filtros Telegram |
| `location` | PointField (WGS84) | Coordenadas lat/lon para ingestor y mapa |
| `altitude_m` | Integer | Altitud en metros (opcional) |
| `is_active` | Boolean | Incluir en ciclos de ingestión y predicción |

El mapa del dashboard (`/weather/map`) muestra marcadores coloreados con el nivel de alerta activo más alto de cada estación.

---

## Versioning

`MAJOR.MINOR.PATCH` — fix → PATCH | feature → MINOR

Versión actual: **v0.11.4**

Changelog: [`CHANGELOG.md`](CHANGELOG.md)
