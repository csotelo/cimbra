"""Core views — SiteConfig (SEO + skin + robots)."""
import re

from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.models import SiteConfig

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

EDITABLE_FIELDS = [
    "site_name", "site_description", "og_image_url",
    "favicon_url", "allow_indexing", "primary_color",
]


def _serialize(cfg: SiteConfig) -> dict:
    return {
        "site_name": cfg.site_name,
        "site_description": cfg.site_description,
        "og_image_url": cfg.og_image_url,
        "favicon_url": cfg.favicon_url,
        "allow_indexing": cfg.allow_indexing,
        "primary_color": cfg.primary_color,
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
    }


class SiteConfigView(APIView):
    """GET /api/config/site/ — lectura pública.
    PATCH /api/config/site/ — actualización (solo superuser/is_staff).
    """

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        return Response(_serialize(SiteConfig.get_solo()))

    def patch(self, request):
        cfg = SiteConfig.get_solo()
        errors = {}

        for field in EDITABLE_FIELDS:
            if field not in request.data:
                continue
            value = request.data[field]
            if field == "primary_color":
                if not _HEX_COLOR.match(str(value)):
                    errors["primary_color"] = "Debe ser un color hex válido (#rrggbb)."
                    continue
            if field == "allow_indexing" and not isinstance(value, bool):
                errors["allow_indexing"] = "Debe ser true o false."
                continue
            setattr(cfg, field, value)

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        cfg.save()
        return Response(_serialize(cfg))
