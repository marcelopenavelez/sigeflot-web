from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Conductor, Salida, Vehiculo
from .conftest import token


def headers(client, role="CHOFER"):
    return {"Authorization": f"Bearer {token(client, f'{role.lower()}@example.com')}"}


def vehicle(db: Session, estado="OPERATIVO", kilometraje=100):
    item = Vehiculo(placa="TST-001", marca="Marca", modelo="Modelo", anio=2026, tipo="CAMIONETA", kilometraje_actual=kilometraje, estado=estado)
    db.add(item); db.commit(); db.refresh(item)
    return item


def driver(db: Session, email="chofer@example.com"):
    item = Conductor(nombres="Chofer", apellidos="Prueba", email=email, activo=True)
    db.add(item); db.commit()


def test_exit_requires_authentication(client):
    assert client.post("/api/v1/salidas", json={"vehiculo_id": 1, "kilometraje_salida": 1}).status_code == 401


def test_create_exit_updates_vehicle(client, db_session):
    item = vehicle(db_session); driver(db_session)
    response = client.post("/api/v1/salidas", headers=headers(client), json={"vehiculo_id": item.id, "kilometraje_salida": 125, "observaciones": "Salida de prueba"})
    assert response.status_code == 201
    body = response.json()
    assert body["estado"] == "ABIERTA"
    assert body["es_historico"] is False
    assert body["fuente_origen"] == "OPERATIVO"
    assert body["conductor_id"] == db_session.scalar(select(Conductor.id))
    assert datetime.fromisoformat(body["fecha_hora_salida"].replace("Z", "+00:00")) <= datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.rollback()
    db_session.expire_all()
    assert db_session.get(Vehiculo, item.id).kilometraje_actual == 125


def test_exit_requires_linked_driver(client, db_session):
    item = vehicle(db_session)
    assert client.post("/api/v1/salidas", headers=headers(client), json={"vehiculo_id": item.id, "kilometraje_salida": 100}).status_code == 422


def test_exit_validations(client, db_session):
    item = vehicle(db_session); driver(db_session)
    auth = headers(client)
    assert client.post("/api/v1/salidas", headers=auth, json={"vehiculo_id": 999, "kilometraje_salida": 100}).status_code == 404
    assert client.post("/api/v1/salidas", headers=auth, json={"vehiculo_id": item.id, "kilometraje_salida": 99}).status_code == 422
    item.estado = "MANTENIMIENTO"; db_session.commit()
    assert client.post("/api/v1/salidas", headers=auth, json={"vehiculo_id": item.id, "kilometraje_salida": 100}).status_code == 422


def test_exit_rejects_null_current_mileage(client, db_session):
    item = vehicle(db_session, kilometraje=None); driver(db_session)
    response = client.post("/api/v1/salidas", headers=headers(client), json={"vehiculo_id": item.id, "kilometraje_salida": 0})
    assert response.status_code == 422
    assert response.json()["detail"] == "El vehículo no tiene kilometraje actual registrado"


def test_conductor_match_is_case_insensitive(client, db_session):
    item = vehicle(db_session); driver(db_session, "CHOFER@EXAMPLE.COM")
    assert client.post("/api/v1/salidas", headers=headers(client), json={"vehiculo_id": item.id, "kilometraje_salida": 101}).status_code == 201


def test_selector_excludes_non_operational_and_open_exit(client, db_session):
    eligible = vehicle(db_session)
    maintenance = Vehiculo(placa="TST-002", marca="Marca", modelo="Modelo", anio=2026, tipo="CAMIONETA", kilometraje_actual=1, estado="MANTENIMIENTO")
    with_open_exit = Vehiculo(placa="TST-003", marca="Marca", modelo="Modelo", anio=2026, tipo="CAMIONETA", kilometraje_actual=1, estado="OPERATIVO")
    db_session.add_all([maintenance, with_open_exit]); db_session.flush()
    db_session.add(Salida(vehiculo_id=with_open_exit.id, fecha_hora_salida=datetime.now(), kilometraje_salida=1, estado="ABIERTA", es_historico=False, fuente_origen="OPERATIVO")); db_session.commit()
    response = client.get("/api/v1/salidas/vehicles", headers=headers(client))
    assert response.status_code == 200
    assert response.json() == [{"id": eligible.id, "placa": eligible.placa, "marca": "Marca", "modelo": "Modelo", "kilometraje_actual": 100, "estado": "OPERATIVO"}]


def test_open_exit_and_rbac(client, db_session):
    item = vehicle(db_session); driver(db_session); driver(db_session, "mecanico@example.com")
    auth = headers(client)
    assert client.post("/api/v1/salidas", headers=auth, json={"vehiculo_id": item.id, "kilometraje_salida": 110}).status_code == 201
    assert client.post("/api/v1/salidas", headers=auth, json={"vehiculo_id": item.id, "kilometraje_salida": 111}).status_code == 409
    assert client.get("/api/v1/salidas/vehicles", headers=headers(client, "CONSULTA")).status_code == 403
    assert client.post("/api/v1/salidas", headers=headers(client, "CONSULTA"), json={"vehiculo_id": item.id, "kilometraje_salida": 110}).status_code == 403
    assert client.get("/api/v1/salidas/vehicles", headers=headers(client, "MECANICO")).status_code == 200
