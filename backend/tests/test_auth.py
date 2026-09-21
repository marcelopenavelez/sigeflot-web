import jwt
from app.core.security import create_access_token, hash_password, verify_password
from .conftest import token

def test_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/health/db").status_code == 200

def test_password_hashing():
    first, second = hash_password("PasswordSeguro!1"), hash_password("PasswordSeguro!1")
    assert verify_password("PasswordSeguro!1", first) and not verify_password("OtraPassword!1", first)
    assert "PasswordSeguro!1" not in first and first != second

def test_login_and_me(client):
    response = client.post("/api/v1/auth/login", json={"email":"administrador@example.com","password":"PasswordSeguro!1"})
    assert response.status_code == 200 and response.json()["token_type"] == "bearer"
    me = client.get("/api/v1/auth/me", headers={"Authorization":f"Bearer {response.json()['access_token']}"})
    assert me.status_code == 200 and me.json()["rol"] == "ADMINISTRADOR" and "password_hash" not in me.json()

def test_login_rejections(client):
    for email, password in [("nadie@example.com","PasswordSeguro!1"),("administrador@example.com","PasswordMala!1"),("inactivo@example.com","PasswordSeguro!1")]:
        assert client.post("/api/v1/auth/login", json={"email":email,"password":password}).status_code == 401

def test_token_rejections(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization":"Bearer invalid"}).status_code == 401
    expired = jwt.encode({"sub":"1","role":"ADMINISTRADOR","exp":0}, "pytest-isolated-secret-key-which-is-long-enough", algorithm="HS256")
    assert client.get("/api/v1/auth/me", headers={"Authorization":f"Bearer {expired}"}).status_code == 401

def test_admin_user_operations(client, admin_headers):
    payload={"nombres":"Nuevo","apellidos":"Usuario","email":"nuevo@example.com","password":"PasswordSeguro!1","role_code":"CONSULTA"}
    assert client.post("/api/v1/users",json=payload,headers=admin_headers).status_code == 201
    assert client.post("/api/v1/users",json=payload,headers=admin_headers).status_code == 409
    assert client.get("/api/v1/users",headers=admin_headers).status_code == 200

def test_rbac_and_validation(client):
    payload={"nombres":"Nuevo","apellidos":"Usuario","email":"nuevo@example.com","password":"PasswordSeguro!1","role_code":"CONSULTA"}
    for role in ("mecanico","chofer","consulta"):
        headers={"Authorization":f"Bearer {token(client, role+'@example.com')}"}
        assert client.post("/api/v1/users",json=payload,headers=headers).status_code == 403
        assert client.get("/api/v1/users",headers=headers).status_code == 403
    assert client.post("/api/v1/users",json={**payload,"email":"bad"},headers={"Authorization":f"Bearer {token(client)}"}).status_code == 422
    assert client.post("/api/v1/users",json={**payload,"password":"short"},headers={"Authorization":f"Bearer {token(client)}"}).status_code == 422

def test_openapi(client):
    spec=client.get("/openapi.json").json()
    assert client.get("/docs").status_code == 200
    assert "/api/v1/auth/login" in spec["paths"] and "/api/v1/users" in spec["paths"]
