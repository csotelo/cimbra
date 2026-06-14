# Changelog

All notable changes to Ximbra are documented here.
Versioning: MAJOR.MINOR.PATCH — fix = PATCH, feature = MINOR.

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
