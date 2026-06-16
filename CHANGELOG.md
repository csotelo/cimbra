# Changelog

All notable changes to Ximbra are documented here.
Versioning: MAJOR.MINOR.PATCH — fix = PATCH, feature = MINOR.

---

## [0.15.0] - 2026-06-15

### Sprint 4 — Alertas sonoras de campo: FCM push + buzzer Flutter + motor de distancias

#### Backend — motor de alertas de distancia
- `firebase-admin==6.6.0` añadido a `requirements.txt`
- `apps/field/fcm.py` — utilidad `send_fcm_push(token, title, body, data)`: inicializa Firebase con `FIREBASE_CREDENTIALS_JSON` desde env, envía push con prioridad alta Android, graceful fallback si no configurado
- `apps/field/tasks.py` — Celery task `field.check_field_alerts` (cada 60 s):
  - Lee posiciones actuales desde Redis `tracking:last_position:{tenant_id}`
  - Calcula distancia Haversine desde cada empleado a cada estación con alerta activa
  - 0–16 km → Alerta Roja (FCM zumbido continuo)
  - 16–32 km → Alerta Amarilla (FCM zumbido entrecortado)
  - Cooldown de 5 min por empleado para evitar spam (verifica `last_alert_sent_at` y nivel)
  - Escribe nivel de alerta actual en Redis `tracking:field_alert:{employee_id}` (TTL 2 h)
  - Actualiza `Employee.last_alert_level` + `Employee.last_alert_sent_at` en DB
- `apps/field/models.py` — campos `last_alert_level` + `last_alert_sent_at` en Employee
- Migración `field/0004_employee_alert_tracking`
- `settings/base.py` — `FIREBASE_CREDENTIALS_JSON` desde env, beat schedule `check-field-alerts` cada 60 s
- `TrackingLiveView` — enriquece cada posición con `field_alert` (level, station, distance_km) desde Redis
- `.env.example` — `FIREBASE_CREDENTIALS_JSON`, `MQTT_PORT`

#### Frontend — indicadores visuales de alerta
- `TrackingMap.vue` — anillo pulsante de color alrededor de marcadores según nivel (rojo/naranja/amarillo), badge de alerta en panel lateral, popup con distancia y estación
- `SafetyMap.vue` — mismo sistema de anillos en posiciones en vivo del mapa de seguridad integrado

#### Móvil Flutter — buzzer de alerta sonora
- `pubspec.yaml` — add `vibration: ^2.0.0`
- `services/fcm_service.dart` — inicializa FCM, recibe mensajes foreground/background/terminated, activa buzzer según nivel:
  - Nivel 4 (Rojo): patrón continuo `[500,200,500,200,500,200]`, se repite cada 8 s
  - Nivel 3 (Naranja): patrón rápido `[300,400,300,400]`
  - Nivel 2 (Amarillo): patrón lento `[200,800,200,800]`
  - Nivel 1: detiene vibración
- `services/fcm_service.dart` — `AlertBanner` widget: banner rojo/naranja/amarillo con título, descripción y botón de dismiss que también detiene el buzzer
- `screens/map_screen.dart` — integra FCM stream, muestra AlertBanner en overlay sobre el mapa al recibir push
- `main.dart` — inicializa Firebase.initializeApp() + FcmService().init() al arrancar

---

## [0.14.0] - 2026-06-15

### Sprint 3 — Refugios Fijos y Mapa de Seguridad Integrado

#### Backend — nuevo modelo en `field`
- Modelo `RefugePoint` — punto de refugio fijo (UUID, tenant, name, description, PointField geography=True SRID=4326, capacity, project FK, is_active)
- Migración `field/0003_refuge_point`
- `RefugePointViewSet` — CRUD + toggle + acción `GET /api/field/points/geojson/` (GeoJSON FeatureCollection para Leaflet)
- `RefugePointSerializer` + `RefugePointGeoSerializer` (GeoFeatureModelSerializer)
- Admin: `RefugePointAdmin` (GISModelAdmin con mapa interactivo)

#### Frontend — módulo Campo
- `RefugePointMap.vue` — mapa Leaflet: clic en mapa para posicionar punto, modal nombre/descripción/capacidad/proyecto, marcadores verdes tipo escudo, panel lateral de lista, eliminar punto
- `SafetyMap.vue` — mapa de seguridad integrado con 5 capas:
  - Frentes de trabajo (polígonos índigo, `/api/field/fences/geojson/`)
  - Refugios fijos (marcadores verdes, `/api/field/points/geojson/`)
  - Posiciones en vivo empleados/refugios móviles (polling 5 s, `/api/field/tracking/live/`)
  - Estaciones meteorológicas (marcadores cian, `/api/weather/stations/geojson/`)
  - Panel lateral: alertas activas por nivel de color + unidades GPS en campo
- Rutas nuevas: `/campo/refugios-fijos`, `/campo/mapa-seguridad`

#### Móvil — app Flutter
- `services/api_service.dart` — cliente HTTP para `/api/field/points/geojson/` con Bearer token
- `screens/refuge_screen.dart` — lista de puntos de refugio ordenados por distancia al usuario,
  indicador de color (verde ≤500 m, naranja ≤2 km, rojo > 2 km), recarga manual
- `screens/map_screen.dart` — FAB "Refugios" abre refuge_screen con posición actual
- `screens/login_screen.dart` — campos opcionales: URL base API + JWT token del admin

---

## [0.13.0] - 2026-06-15

### Sprint 2 — Rastreo GPS en tiempo real: MQTT + Refugios Móviles + Flutter

#### Backend — nuevos modelos en `field`
- Modelo `MobileRefuge` — unidad de refugio móvil (UUID, tenant, code, plate, capacity, conductor FK Employee, project FK, is_active). Posición = posición GPS del conductor via MQTT.
- Modelo `EmployeePosition` — serie temporal de posiciones GPS (BigAutoField, tenant FK, entity_id UUID, entity_type, lat, lon, accuracy, recorded_at, received_at). Índice compuesto (tenant, entity_id, -recorded_at).
- Migración `field/0002_mobile_refuge_position`
- `MobileRefugeViewSet` — CRUD + toggle activo/inactivo, filtrado por tenant
- `TrackingLiveView` (`GET /api/field/tracking/live/`) — lee HGETALL de Redis `tracking:last_position:{tenant_id}`, enriquece con nombres de empleados y refugio móvil asociado si el conductor coincide
- Admin: `MobileRefugeAdmin`

#### Infraestructura — servicios nuevos en docker-compose
- `mosquitto` — eclipse-mosquitto:2, port `${MQTT_PORT:-1883}:1883` expuesto externamente para dispositivos móviles de campo
- `mosquitto/mosquitto.conf` — allow_anonymous true, persistencia en volumen `mosquitto_data`
- `gps_tracker` — servicio Python asyncio (aiomqtt + asyncpg + redis):
  - Suscribe topic `ximbra/+/tracking/+/+/position`
  - Escribe posición actual en Redis Hash `tracking:last_position:{tenant_id}` (TTL 24 h)
  - Buffer en memoria, escribe en lote a `field_positions` cada 10 s o 500 mensajes
  - Auto-reconexión MQTT ante desconexiones

#### Frontend — módulo Campo
- `MobileRefugeList.vue` — CRUD de unidades (código, placa, capacidad, conductor, proyecto), toggle activo/inactivo
- `TrackingMap.vue` — mapa Leaflet en tiempo real: polling `/api/field/tracking/live/` cada 5 s, marcadores diferenciados (índigo = empleado, naranja = refugio móvil), panel lateral con posiciones, centrar al hacer clic
- Rutas nuevas: `/campo/refugios-moviles`, `/campo/rastreo`

#### Móvil — app Flutter `mobile/`
- `pubspec.yaml` — deps: mqtt_client, geolocator, flutter_map, latlong2, flutter_secure_storage, firebase_core/messaging
- `main.dart` — router de splash que verifica credenciales guardadas
- `screens/login_screen.dart` — ingresa tenant_id, employee_id, nombre (guarda en secure storage)
- `screens/map_screen.dart` — mapa FlutterMap con posición propia, publica GPS por MQTT cada 30 s
- `services/location_service.dart` — GPS stream con geolocator (alta precisión, filtro 10 m)
- `services/mqtt_service.dart` — cliente MQTT, publica JSON `{lat, lon, accuracy, ts}` al topic configurado
- `config/app_config.dart` — MQTT_HOST/PORT configurables por env en build time

---

## [0.12.0] - 2026-06-15

### Sprint 1 — Campo: Empleados, Proyectos y Frentes de Trabajo (US29/US30/US31)

#### Backend — app `field` (nueva)
- Modelo `Employee` — empleado de campo (UUID, tenant, full_name, document_number, device_id único, fcm_token, photo, is_active)
- Modelo `Project` — proyecto/obra (UUID, tenant, name, description, start_date, end_date, M2M employees, is_active)
- Modelo `GeoFence` — frente de trabajo (UUID, tenant, project, name, PolygonField geography=True SRID=4326, is_active)
- Migración `field/0001_initial` con índices (tenant+is_active, device_id, project)
- DRF ViewSets: `EmployeeViewSet`, `ProjectViewSet`, `GeoFenceViewSet` — todos filtrados por tenant
- Acción `POST /api/field/employees/{id}/toggle/` — toggle is_active
- Acción `POST /api/field/projects/{id}/assign_employees/` — asigna M2M empleados al proyecto
- Endpoint `GET /api/field/fences/geojson/` — GeoJSON FeatureCollection para Leaflet
- Admin Django: `EmployeeAdmin`, `ProjectAdmin`, `GeoFenceAdmin` (con GISModelAdmin para polígonos)
- Registro automático vía `vigilo_module = True` en `FieldConfig`

#### Frontend — módulo Campo
- `EmployeeList.vue` — CRUD empleados: listar, crear, editar, toggle activo/inactivo, búsqueda por nombre
- `ProjectList.vue` — CRUD proyectos: listar en cards, crear, editar con fecha inicio/fin
- `ProjectDetail.vue` — detalle de proyecto con asignación de empleados (modal M2M)
- `GeoFenceMap.vue` — mapa Leaflet con control de dibujo (leaflet-draw), guardar polígono como frente de trabajo, overlay de frentes existentes por proyecto, eliminar frente
- Rutas nuevas: `/campo/empleados`, `/campo/proyectos`, `/campo/proyectos/:id`, `/campo/frentes`
- Grupo "Campo" en menú lateral con orden 20 (entre Meteorología y Administración)
- `leaflet-draw ^1.0.4` añadido a `package.json`

---

## [0.1.0] - 2026-06-14

### Fase 0 — Recovery email templates
- Templates movidos a `backend/templates/emails/` (BASE_DIR 3 parents)
- Eliminado volumen `./templates` del docker-compose
- Red Docker renombrada a `ximbra_app_network`

### Fase 1 — US01: Modo Uni-Tenant
- `SINGLE_TENANT_MODE` + `MAIN_TENANT_SLUG` en settings y `.env.example`
- `TenantMiddleware` fuerza tenant principal cuando flag activo
- Signal `post_save(CustomUser)` auto-join MEMBER al tenant principal
- `GET /api/config/` endpoint público para el frontend
- Frontend oculta UI multi-tenant cuando `SINGLE_TENANT_MODE=True`
- Branding: Ximbra en admin, layout y emails

### Fase 1 — US02: Invitaciones por email
- Modelo `Invitation` (email, token UUID, invited_by, expires_at 72h, accepted_at)
- Migración `0003_invitation`
- Celery task `send_invitation_email` con templates HTML + TXT
- `POST /api/users/invitations/` — crea y envía invitación async
- `GET /api/users/invitations/{token}/` — valida token, devuelve email pre-cargado
- `POST /api/users/invitations/{token}/` — acepta: crea usuario + une al tenant
- Django admin `InvitationAdmin` con badge de estado
- Frontend: botón "Invitar por email" en MemberList + vista `AcceptInvitation.vue`
