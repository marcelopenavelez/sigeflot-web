import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url


# ---------------------------------------------------------
# Configuración aislada para pruebas
# ---------------------------------------------------------

from app.core.config import get_settings

# Toma las credenciales reales de backend/.env
base_url = make_url(get_settings().database_url)

# Cambia únicamente la base de datos a la base de pruebas
test_url = base_url.set(database="sigeflot_test")

os.environ["DATABASE_URL"] = test_url.render_as_string(
    hide_password=False
)

# Obliga a FastAPI a volver a leer la configuración
get_settings.cache_clear()


# ---------------------------------------------------------
# Imports de la aplicación después de configurar TEST DB
# ---------------------------------------------------------

from fastapi.testclient import TestClient

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.models import Base, Role, Usuario

TEST_PASSWORD_HASH = hash_password("PasswordSeguro!1")


# Protección: nunca ejecutar pruebas sobre la BD principal
assert str(engine.url).split("?")[0].endswith("/sigeflot_test"), (
    "Pytest debe ejecutarse únicamente sobre sigeflot_test"
)


# ---------------------------------------------------------
# Preparación de la base de datos
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def schema():
    with engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        Base.metadata.drop_all(connection)
        connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        roles = {}

        for code in (
            "ADMINISTRADOR",
            "MECANICO",
            "CHOFER",
            "CONSULTA",
        ):
            role = Role(
                codigo=code,
                nombre=code,
                activo=True,
            )
            db.add(role)
            roles[code] = role

        db.flush()

        for code, role in roles.items():
            usuario = Usuario(
                nombres=code,
                apellidos="Prueba",
                email=f"{code.lower()}@example.com",
                password_hash=TEST_PASSWORD_HASH,
                role_id=role.id,
                activo=True,
            )
            db.add(usuario)

        usuario_inactivo = Usuario(
            nombres="Inactivo",
            apellidos="Prueba",
            email="inactivo@example.com",
            password_hash=TEST_PASSWORD_HASH,
            role_id=roles["CONSULTA"].id,
            activo=False,
        )

        db.add(usuario_inactivo)
        db.commit()

    yield


# ---------------------------------------------------------
# Cliente FastAPI
# ---------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------
# Token JWT para pruebas
# ---------------------------------------------------------

def token(
    client,
    email="administrador@example.com",
):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "PasswordSeguro!1",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ---------------------------------------------------------
# Cabecera ADMINISTRADOR
# ---------------------------------------------------------

@pytest.fixture
def admin_headers(client):
    return {
        "Authorization": f"Bearer {token(client)}"
    }
