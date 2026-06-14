"""FastAPI main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import process as process_router
from app.api.routes import validate as validate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    yield
    from app.api.dependencies import container

    if container._postgres is not None:
        container._postgres.close()
    if container._redis is not None:
        container._redis.close()


app = FastAPI(
    title="Multi-Tenant API",
    version="1.0.0",
    description="FastAPI service for multi-tenant API processing with "
    "hexagonal architecture. Validates tokens, enforces rate limits, "
    "and processes requests.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process_router.router)
app.include_router(validate_router.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
