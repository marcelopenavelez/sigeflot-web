from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import SessionLocal
from app.core.config import get_settings
from app.api.auth import router as auth_router
from app.api.users import router as users_router

app = FastAPI(title="SIGEFLOT WEB API", description="API base del Sistema Integral de Gestión de Flota y Mantenimiento Vehicular.", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    """Return an identifier for the API."""
    return {"message": "SIGEFLOT WEB API"}


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Expose a lightweight service health check."""
    return {"status": "ok", "service": "sigeflot-api"}


@app.get("/health/db", tags=["system"])
def database_health_check() -> dict[str, str]:
    """Check database availability without disclosing connection details."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        return {"status": "unavailable", "database": "disconnected"}
