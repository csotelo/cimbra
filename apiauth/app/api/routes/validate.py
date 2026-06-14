"""Token validation endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import container
from app.api.routes.process import extract_token, get_postgres_connection, get_redis_url

router = APIRouter(prefix="/api/v1", tags=["validate"])


class TokenValidationResponse(BaseModel):
    valid: bool
    tenant_id: str
    tenant_name: str
    user_email: str
    role: str
    message: str


@router.get(
    "/validate",
    response_model=TokenValidationResponse,
    responses={
        200: {"description": "Token válido"},
        401: {"description": "Token inválido o expirado"},
    },
    summary="Valida un API token",
    description=(
        "Verifica que el token existe, está activo, no ha expirado "
        "y pertenece a un tenant y usuario activos. "
        "No consume rate limit."
    ),
)
def validate_token(
    authorization: Annotated[str | None, Header()] = None,
    x_api_token: Annotated[str | None, Header()] = None,
    postgres_connection: str = Depends(get_postgres_connection),
    redis_url: str = Depends(get_redis_url),
) -> TokenValidationResponse:
    """Valida el token y retorna los datos asociados sin consumir rate limit."""
    token = extract_token(authorization, x_api_token)
    use_case = container.get_validate_token(postgres_connection, redis_url)
    result = use_case.execute(token)

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message,
        )

    return TokenValidationResponse(
        valid=True,
        tenant_id=str(result.tenant.id),
        tenant_name=result.tenant.name,
        user_email=result.user.email,
        role=result.role.role,
        message="Token válido",
    )
