# Changelog

All notable changes to Ximbra are documented here.
Versioning: MAJOR.MINOR.PATCH — fix = PATCH, feature = MINOR.

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
