# Ximbra — Sistema de Alertas de Tormentas Eléctricas

Sistema de predicción y alerta temprana de tormentas eléctricas para Perú, basado en IA y datos meteorológicos en tiempo real. Combina una plataforma multi-tenant SaaS con un pipeline de Machine Learning de extremo a extremo.

---

## Índice

1. [Visión general](#visión-general)
2. [Arquitectura del sistema](#arquitectura-del-sistema)
3. [Pipeline de datos e IA](#pipeline-de-datos-e-ia)
4. [Módulo de Campo — GPS, MQTT y alertas móviles](#módulo-de-campo--gps-mqtt-y-alertas-móviles)
5. [Stack tecnológico](#stack-tecnológico)
6. [Servicios y contenedores](#servicios-y-contenedores)
7. [Modelos de datos](#modelos-de-datos)
8. [API REST — endpoints](#api-rest--endpoints)
9. [FastAPI — validación y rate limiting](#fastapi--validación-y-rate-limiting)
10. [Frontend](#frontend)
11. [App móvil Flutter](#app-móvil-flutter)
12. [Variables de entorno](#variables-de-entorno)
13. [Despliegue en producción](#despliegue-en-producción)
14. [Configuración de estaciones](#configuración-de-estaciones)

---

## Visión general

Ximbra ingiere variables meteorológicas horarias de la API pública **Open-Meteo**, las procesa con modelos de red neuronal (**MLP / LSTM**) calibrados con Platt Scaling, genera alertas de tormenta según la escala SENAMHI (Verde / Amarillo / Naranja / Rojo) y las distribuye a través de un dashboard web, un bot de Telegram y, desde la v0.12, una app móvil de campo con rastreo GPS y zumbido de alerta.

> **¿Ximbra usa LLMs (modelos de lenguaje tipo GPT/Claude)?** No. Los "modelos de IA" de Ximbra son redes neuronales numéricas pequeñas (MLP/LSTM, descritas en detalle en [Pipeline de datos e IA](#pipeline-de-datos-e-ia)) que reciben 5 variables meteorológicas y devuelven una probabilidad de tormenta entre 0 y 1. No generan texto, no conversan, no son modelos de lenguaje — son clasificadores entrenados con datos históricos de Open-Meteo. No hay ningún LLM ni API de OpenAI/Anthropic en el stack de predicción.

La plataforma es multi-tenant con aislamiento lógico: múltiples organizaciones comparten la misma base de datos con separación por software.

```
Open-Meteo API ──► Ingestor ──► PostgreSQL/PostGIS ──► Predictor ──► StormAlerts
                                                              │
                                                        Trainer (ML)
                                                              │
                                                     Django Admin + Vue SPA
                                                              │
                                          ┌───────────────────┴───────────────────┐
                                          │                                       │
                                   Telegram Bot                     Motor de alertas de Campo
                                                                     (distancia empleado↔estación)
                                                                              │
                                                                    FCM push ──► App Flutter
                                                                                  (zumbido)
```

El módulo de Campo añade un segundo flujo de datos, independiente del meteorológico: dispositivos móviles de trabajadores envían su posición GPS por MQTT en tiempo real, y un motor calcula su distancia a la estación con alerta activa más cercana para decidir si deben recibir una notificación push con zumbido. Ver el detalle completo en [Módulo de Campo](#módulo-de-campo--gps-mqtt-y-alertas-móviles).

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CLIENTE (Browser)                          App móvil Flutter (campo)   │
│  Vue 3 SPA — Tailwind CSS — Pinia — Axios    GPS + MQTT + FCM            │
└───────────────────────────┬───────────────────────────┬─────────────────┘
                            │ HTTP :80                  │ MQTT :1883
┌───────────────────────────▼───────────────┐  ┌─────────▼─────────────────┐
│  nginx (vue container)                     │  │  mosquitto (broker MQTT)  │
│  /         → static SPA                    │  │  expuesto al exterior     │
│  /api/*    → proxy_pass http://django:8000 │  │  para dispositivos campo  │
│  /ws/*     → proxy_pass ws://django:8000   │  └─────────┬─────────────────┘
└─────────┬───────────────────────────────────┘            │ pub/sub posiciones
          │ red interna ximbra_app_network                 │
          │                                       ┌─────────▼─────────────────┐
┌─────────▼──────────┐    ┌──────────────────┐    │  gps_tracker (asyncio)    │
│  Django :8000      │    │  FastAPI :8001    │    │  Redis hash posición      │
│  DRF + Channels    │    │  Hexagonal arch.  │    │  Batch insert PostgreSQL  │
│  Admin (Unfold)    │    │  Token validation │    └─────────┬─────────────────┘
│  JWT Auth          │    │  Rate limiting    │              │
└────────┬───────────┘    └────────┬──────────┘    ┌─────────▼─────────────────┐
         │                         │                │  Celery Beat (60s)        │
┌────────▼─────────────────────────▼────────────────┤  field.check_field_alerts │
│  PostgreSQL + PostGIS :5432   Redis :6379    Mongo │  distancia → FCM push     │
│  Datos relacionales           Cache/Broker   DB    └────────────────────────────┘
│  Geometrías estaciones        Pub/Sub posiciones
│  Observaciones/Alertas        Rate limits / alert level por empleado
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
│  gps_tracker → MQTT positions → Redis + PostgreSQL (batch)               │
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

## Módulo de Campo — GPS, MQTT y alertas móviles

Desde la v0.12 (junio 2026), Ximbra incorpora un segundo sistema completo pensado para trabajadores que están físicamente en el campo (obras, frentes de trabajo) y necesitan saber, en tiempo real, si una tormenta eléctrica se está acercando a su posición exacta — no solo a la estación meteorológica más cercana.

Este módulo vive en la app `backend/apps/field/`, un servicio Python independiente (`gps_tracker/`), un broker MQTT (`mosquitto`) y una app móvil Flutter (`mobile/`). Es completamente separado del pipeline de IA: no usa redes neuronales, usa geometría simple (distancia) sobre datos que ya generó el predictor.

### ¿Para qué sirve, en palabras simples?

1. Cada empleado de campo lleva el celular con la app Ximbra abierta.
2. El celular manda su ubicación GPS cada 30 segundos a un servidor.
3. Cada 60 segundos, el servidor calcula qué tan lejos está cada empleado de la estación meteorológica más cercana que tiene una alerta de tormenta activa.
4. Si está a menos de 16 km → se le manda una notificación push con zumbido continuo (peligro inmediato, "busca refugio ahora").
5. Si está entre 16 y 32 km → notificación con zumbido intermitente (alerta, mantente atento).
6. Si está más lejos, no recibe nada.
7. Además, el empleado puede ver en su celular un mapa con los puntos de refugio fijos más cercanos (cuevas, casetas, contenedores) ordenados por distancia.

### Modelos de datos del módulo (`backend/apps/field/models.py`)

| Modelo | Qué representa | Campos clave |
|---|---|---|
| `Employee` | Un trabajador de campo. **No** necesariamente tiene cuenta de usuario del sistema — solo necesita el celular con la app. | `full_name`, `document_number`, `device_id` (único, para MQTT), `fcm_token` (para el push), `photo`, `last_alert_level`, `last_alert_sent_at` |
| `Project` | Una obra o proyecto donde trabajan los empleados. | `name`, `start_date`/`end_date`, M2M con `Employee` |
| `GeoFence` | Un "frente de trabajo": un polígono dibujado en el mapa que delimita dónde trabaja un proyecto. | `perimeter` (PolygonField geográfico), FK a `Project` |
| `MobileRefuge` | Una unidad móvil (camioneta, bus) que sirve de refugio. Su posición es la del conductor — no lleva GPS propio, usa el celular del conductor (que es un `Employee`). | `code`, `plate`, `capacity`, `conductor` (FK a Employee) |
| `EmployeePosition` | El histórico de posiciones GPS — una fila por cada posición recibida (no en tiempo real, esto es para reportes/auditoría). | `entity_id`, `entity_type`, `latitude`, `longitude`, `recorded_at` |
| `RefugePoint` | Un punto de refugio fijo (caseta, edificio) marcado en el mapa. | `location` (PointField geográfico), `capacity`, FK a `Project` |

La posición **en vivo** (la de "ahora mismo") no se guarda en PostgreSQL para cada mensaje — eso sería demasiado tráfico a la base de datos. Se guarda en **Redis**, que es mucho más rápido, y solo se escribe en PostgreSQL en lotes (ver siguiente sección).

### De dónde vienen los datos GPS, cuándo y cómo se ingieren

A diferencia del clima (que viene de una API externa, Open-Meteo), los datos de posición GPS vienen de los **propios celulares de los empleados** — son datos generados por el sistema mismo, no una fuente externa. El flujo es:

```
1. App Flutter (celular del empleado)
   └─ Cada 30 segundos (AppConfig.publishIntervalSec) lee el GPS del celular
      y publica un mensaje MQTT al tópico:
      ximbra/{tenant_id}/tracking/employee/{employee_id}/position
      Contenido: { "lat": -12.04, "lon": -77.03, "accuracy": 8.5, "ts": "2026-06-16T10:00:00Z" }

2. mosquitto (broker MQTT, puerto 1883 — el único puerto de este módulo expuesto a Internet,
   porque los celulares deben poder conectarse desde cualquier red)
   └─ Recibe el mensaje y lo reenvía a quien esté suscrito al tópico ximbra/+/tracking/+/+/position

3. gps_tracker (servicio Python asyncio, corre dentro de la red Docker, sin puertos expuestos)
   └─ Está suscrito permanentemente a ese tópico MQTT
   └─ Por cada mensaje recibido:
        a) Escribe inmediatamente en Redis (HSET tracking:last_position:{tenant_id}) —
           esto es lo que ve el mapa en vivo del dashboard, con 24h de vigencia (TTL)
        b) Lo guarda en un buffer en memoria
   └─ Cada 10 segundos O cada 500 mensajes acumulados (lo que ocurra primero),
      vacía el buffer en un solo INSERT por lotes a la tabla field_positions
      de PostgreSQL (para tener histórico, no para tiempo real)
   └─ Si se desconecta del broker MQTT, reintenta la conexión cada 5 segundos
      automáticamente — no requiere intervención manual
```

**Resumen para quien no es técnico:** los datos GPS no se "descargan" de ningún sitio externo como el clima — se reciben en tiempo real de cada celular conectado, se guardan al instante en una memoria rápida (Redis) para el mapa en vivo, y cada 10 segundos se respaldan en lote en la base de datos permanente para no perderlos.

### Motor de alertas por distancia (`backend/apps/field/tasks.py`)

Esta es la tarea Celery `field.check_field_alerts`, programada para correr **cada 60 segundos** (`CELERY_BEAT_SCHEDULE`). Es completamente independiente del modelo de IA — no predice nada nuevo, solo usa las alertas (`StormAlert`) que el `predictor` ya generó y calcula geometría:

```
Cada 60 segundos:
  1. Buscar todas las StormAlert activas con nivel ≥ 2 (Amarillo o peor)
     → de ahí saco la ubicación (lat/lon) de cada estación en alerta

  2. Para cada tenant, leer de Redis las posiciones en vivo de todos sus empleados

  3. Para cada empleado, calcular la distancia (fórmula de Haversine — distancia
     en línea recta sobre la esfera terrestre) a CADA estación en alerta,
     y quedarme con la más cercana:

       distancia ≤ 16 km   →  Nivel 4 — Rojo    (zumbido continuo)
       16 km < distancia ≤ 32 km → Nivel 2 — Amarillo (zumbido intermitente)
       distancia > 32 km   →  Nivel 1 — Verde   (sin alerta, no se envía nada)

  4. Si el nivel calculado es ≥ 2, revisar el "cooldown": no se reenvía la misma
     alerta al mismo empleado si ya se le envió hace menos de 5 minutos Y el nivel
     no cambió (evita saturarlo de notificaciones repetidas)

  5. Si pasa el cooldown, enviar push FCM al celular del empleado con título,
     cuerpo del mensaje, nivel y distancia — y guardar el nuevo nivel/fecha
     en Employee.last_alert_level / last_alert_sent_at

  6. Guardar el nivel actual en Redis (tracking:field_alert:{employee_id}, TTL 2h)
     para que el mapa en vivo del dashboard también pinte el anillo de color
     correcto alrededor del marcador del empleado
```

### Notificaciones push (FCM) — `backend/apps/field/fcm.py`

Se usa **Firebase Cloud Messaging** (Google) para enviar las notificaciones push al celular, vía la librería `firebase-admin`. La credencial de servicio se configura una sola vez en `.env` (`FIREBASE_CREDENTIALS_JSON`, el JSON de cuenta de servicio que se descarga desde Firebase Console). Si esa variable no está configurada, el sistema simplemente no envía push (no falla) — útil para ambientes de desarrollo sin Firebase configurado.

### Vista en vivo para el dashboard — `TrackingLiveView`

El endpoint `GET /api/field/tracking/live/` lee directamente de Redis (no de PostgreSQL, para que sea instantáneo) las últimas posiciones de todos los empleados y refugios móviles del tenant activo, las enriquece con el nombre del empleado y el nivel de alerta actual, y las entrega al frontend. El mapa Vue (`TrackingMap.vue` / `SafetyMap.vue`) hace polling a este endpoint cada 5 segundos.

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
| firebase-admin | 6.6.0 | Envío de notificaciones push (FCM) a la app móvil |

### Módulo de Campo (GPS / MQTT)

| Tecnología | Versión | Rol |
|---|---|---|
| Eclipse Mosquitto | 2 | Broker MQTT — recibe posiciones GPS de los celulares |
| aiomqtt | 2.3.0 | Cliente MQTT asíncrono (servicio `gps_tracker`) |
| asyncpg | 0.29.0 | Cliente PostgreSQL asíncrono para batch insert de posiciones |
| redis (asyncio) | 5.2.1 | Lectura/escritura de posiciones en vivo |

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
| Mosquitto (MQTT) | `eclipse-mosquitto:2` | **1883** (público — celulares de campo) |
| gps_tracker | Python 3.12 (build) | interno (sin puertos expuestos) |

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
├── telegram_bot  ciclo 5min — envía alertas pendientes a suscriptores Telegram
│
├── mosquitto     broker MQTT — recibe posiciones GPS de celulares de campo
└── gps_tracker   ciclo continuo (asyncio) — MQTT → Redis (vivo) + PostgreSQL (lote 10s)
```

celery_beat también dispara `field.check_field_alerts` cada 60 segundos (motor de distancia del módulo de Campo, ver sección dedicada).

### Ciclos temporales configurables

| Servicio | Variable de entorno | Default |
|---|---|---|
| ingestor | `INGESTOR_CYCLE_SEC` | 3600 (1h) |
| predictor | `PREDICTOR_CYCLE_SEC` | 3600 (1h) |
| telegram_bot | `TELEGRAM_NOTIFIER_CYCLE_SEC` | 300 (5 min) |
| gps_tracker (batch a PostgreSQL) | `BATCH_INTERVAL_SEC` | 10 s (o cada 500 mensajes) |
| field.check_field_alerts (Celery Beat) | fijo en código | 60 s |
| App Flutter (publicación GPS) | `publishIntervalSec` (app_config.dart) | 30 s |

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

### Módulo de Campo (`apps/field/`)

```
Project (obra)
    │
    ├──[M2M]──► Employee (trabajador, lleva el celular con la app)
    │                │
    │                └──► last_alert_level / last_alert_sent_at (alerta más reciente)
    │
    ├──► GeoFence (frente de trabajo — polígono geográfico)
    │
    ├──► MobileRefuge (unidad móvil de refugio)
    │         conductor → FK Employee (la posición del refugio = posición de su conductor)
    │
    └──► RefugePoint (punto de refugio fijo — coordenada geográfica)

EmployeePosition (histórico GPS — una fila por mensaje recibido, para auditoría/reportes)
    entity_id · entity_type · latitude · longitude · accuracy · recorded_at

Redis (no es un modelo Django, pero es donde vive el dato "en vivo"):
    tracking:last_position:{tenant_id}   → hash con la última posición de cada entidad (TTL 24h)
    tracking:field_alert:{employee_id}   → nivel de alerta actual de ese empleado (TTL 2h)
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

### Campo — GPS y alertas móviles (`/api/field/`)

Todos los endpoints CRUD requieren JWT y filtran automáticamente por el tenant activo.

| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `employees/` | CRUD de empleados de campo |
| POST | `employees/<id>/toggle/` | Activar/desactivar empleado |
| GET/POST | `projects/` | CRUD de proyectos/obras |
| POST | `projects/<id>/toggle/` | Activar/desactivar proyecto |
| POST | `projects/<id>/assign_employees/` | Asignar empleados a un proyecto |
| GET/POST | `fences/` | CRUD de frentes de trabajo (polígonos) |
| GET | `fences/geojson/` | Frentes activos en GeoJSON para Leaflet |
| GET/POST | `refuges/` | CRUD de unidades de refugio móvil |
| POST | `refuges/<id>/toggle/` | Activar/desactivar unidad |
| GET/POST | `points/` | CRUD de puntos de refugio fijo |
| GET | `points/geojson/` | Puntos activos en GeoJSON (usado también por la app móvil) |
| GET | `tracking/live/` | Posiciones en vivo (desde Redis) de empleados y refugios móviles, con nivel de alerta actual |

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
| `/campo/empleados` | EmployeeList.vue | CRUD de empleados de campo |
| `/campo/proyectos` | ProjectList.vue | CRUD de proyectos/obras |
| `/campo/proyectos/:id` | ProjectDetail.vue | Detalle de proyecto + asignación de empleados |
| `/campo/frentes` | GeoFenceMap.vue | Dibujar/editar frentes de trabajo en mapa Leaflet |
| `/campo/refugios-moviles` | MobileRefugeList.vue | CRUD de unidades de refugio móvil |
| `/campo/rastreo` | TrackingMap.vue | Mapa en vivo de posiciones GPS + nivel de alerta |
| `/campo/refugios-fijos` | RefugePointMap.vue | Marcar puntos de refugio fijo en el mapa |
| `/campo/mapa-seguridad` | SafetyMap.vue | Vista integrada: frentes + refugios + GPS en vivo + estaciones + alertas |

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

## App móvil Flutter

App nativa (`mobile/`) que usan los empleados de campo. No requiere usuario del sistema (Django), solo un `employee_id` registrado por el administrador.

### Flujo de uso

```
1. Login (login_screen.dart) — el empleado ingresa tenant_id + employee_id + nombre
   (datos que le da el administrador). Se guardan cifrados en el celular
   (flutter_secure_storage) para no pedirlos de nuevo.

2. Pantalla de mapa (map_screen.dart) — al abrir:
   a) Pide permiso de ubicación al sistema operativo
   b) Empieza a leer el GPS (geolocator, alta precisión, actualiza si se mueve > 10 m)
   c) Se conecta al broker MQTT y publica su posición cada 30 segundos
   d) Se suscribe a Firebase Cloud Messaging — si llega una alerta, vibra el celular
      según el nivel (patrón continuo para Rojo, intermitente para Amarillo)
      y muestra un banner de color en la pantalla
   e) Botón "Refugios" — abre una lista de los puntos de refugio más cercanos,
      ordenados por distancia (calculada en el propio celular)

3. Si el celular se queda sin internet o se pierde la conexión MQTT,
   reintenta sola — el empleado no tiene que hacer nada.
```

### Paquetes principales (`pubspec.yaml`)

| Paquete | Rol |
|---|---|
| `mqtt_client` | Publica la posición GPS por MQTT |
| `geolocator` | Lee el GPS del celular |
| `flutter_map` + `latlong2` | Mapa interactivo (sin depender de Google Maps) |
| `firebase_messaging` | Recibe las notificaciones push (FCM) |
| `vibration` | Activa el zumbido del celular según el nivel de alerta |
| `flutter_secure_storage` | Guarda las credenciales cifradas en el dispositivo |

> El servidor MQTT (`MQTT_HOST`) y el resto de configuración de conexión se definen en build-time en `mobile/lib/config/app_config.dart` — no requiere recompilar para apuntar a otro entorno si se usa `--dart-define`.

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

# ── Firebase / FCM — alertas push a dispositivos de campo ─────
# JSON de cuenta de servicio de Firebase Console, en una sola línea.
# Si se deja vacío, el sistema simplemente no envía push (no falla).
FIREBASE_CREDENTIALS_JSON=

# ── MQTT Broker (Mosquitto) — rastreo GPS de campo ─────────────
MQTT_PORT=1883
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

[Continuo — automático, módulo de Campo]
  App Flutter → MQTT (cada 30s) → gps_tracker → Redis (vivo) + PostgreSQL (lote 10s)
  Celery Beat (cada 60s) → field.check_field_alerts → distancia a StormAlerts activas
                          → FCM push al celular si está en zona Roja/Amarilla
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

Versión actual: **v0.15.1**

Changelog: [`CHANGELOG.md`](CHANGELOG.md)
