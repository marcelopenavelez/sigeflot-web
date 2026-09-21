import os
os.environ["DATABASE_URL"] = "mysql+pymysql://sigeflot_user:change_me@localhost:3306/sigeflot_test?charset=utf8mb4"
os.environ["JWT_SECRET_KEY"] = "pytest-isolated-secret-key-which-is-long-enough"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.models import Base, Role, Usuario

assert "sigeflot_test" in str(engine.url), "Pytest must only use a _test database"

@pytest.fixture(autouse=True)
def schema():
    with engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0")); Base.metadata.drop_all(connection); connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        roles = {code: Role(codigo=code, nombre=code, activo=True) for code in ("ADMINISTRADOR", "MECANICO", "CHOFER", "CONSULTA")}
        db.add_all(roles.values()); db.flush()
        for code in roles:
            db.add(Usuario(nombres=code, apellidos="Prueba", email=f"{code.lower()}@example.com", password_hash=hash_password("PasswordSeguro!1"), role_id=roles[code].id, activo=True))
        db.add(Usuario(nombres="Inactivo", apellidos="Prueba", email="inactivo@example.com", password_hash=hash_password("PasswordSeguro!1"), role_id=roles["CONSULTA"].id, activo=False)); db.commit()
    yield

@pytest.fixture
def client(): return TestClient(app)

def token(client, email="administrador@example.com"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": "PasswordSeguro!1"}).json()["access_token"]

@pytest.fixture
def admin_headers(client): return {"Authorization": f"Bearer {token(client)}"}
