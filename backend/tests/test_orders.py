from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.orders import is_duplicate_order_error
from app.models import CatalogoMantenimientoOrigen, OrdenServicio, OrdenServicioPreventivo, Proveedor, Vehiculo
from pymysql.err import IntegrityError as MySQLIntegrityError
from sqlalchemy.exc import IntegrityError
from .conftest import token


def headers(client, role="ADMINISTRADOR"):
    return {"Authorization": f"Bearer {token(client, f'{role.lower()}@example.com')}"}


def vehicle(db: Session, *, placa="ORD-001", estado="OPERATIVO", kilometraje=100):
    item = Vehiculo(placa=placa, marca="Marca", modelo="Modelo", anio=2026, tipo="CAMIONETA", kilometraje_actual=kilometraje, estado=estado)
    db.add(item); db.commit(); db.refresh(item)
    return item


def catalog(db: Session, *, component="CAT-001", tarea="Cambio de aceite"):
    item = CatalogoMantenimientoOrigen(id_componente_origen=component, tarea=tarea, prioridad="ALTA", intervalo_km=5000, intervalo_dias=180)
    db.add(item); db.commit(); db.refresh(item)
    return item


def payload(item, **changes):
    result = {"numero_orden": "LOG-001", "vehiculo_id": item.id, "kilometraje_orden": 110, "preventivo_ids": [], "descripcion_correctivo": "Reparación de freno", "estado_archivo": "PENDIENTE"}
    result.update(changes)
    return result


def test_orders_require_authentication(client):
    assert client.post("/api/v1/ordenes-servicio", json={}).status_code == 401
    assert client.get("/api/v1/ordenes-servicio/vehicles").status_code == 401


def test_admin_and_mechanic_can_create_order(client, db_session):
    item = vehicle(db_session)
    assert client.post("/api/v1/ordenes-servicio", headers=headers(client), json=payload(item)).status_code == 201
    assert client.post("/api/v1/ordenes-servicio", headers=headers(client, "MECANICO"), json=payload(item, numero_orden="LOG-002")).status_code == 201


def test_chofer_and_consulta_are_forbidden(client, db_session):
    item = vehicle(db_session)
    for role in ("CHOFER", "CONSULTA"):
        assert client.post("/api/v1/ordenes-servicio", headers=headers(client, role), json=payload(item)).status_code == 403
        assert client.get("/api/v1/ordenes-servicio/maintenance-catalog", headers=headers(client, role)).status_code == 403


def test_order_validates_number_vehicle_and_mileage(client, db_session):
    item = vehicle(db_session)
    auth = headers(client)
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, kilometraje_orden=-1)).status_code == 422
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, kilometraje_orden=99)).status_code == 422
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, vehiculo_id=999)).status_code == 404
    inactive = vehicle(db_session, placa="ORD-002", estado="INACTIVO")
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(inactive, numero_orden="LOG-INA")).status_code == 422
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item)).status_code == 201
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item)).status_code == 409


def test_order_updates_existing_or_null_vehicle_mileage(client, db_session):
    auth = headers(client)
    item = vehicle(db_session)
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, kilometraje_orden=125)).status_code == 201
    db_session.rollback(); db_session.expire_all(); assert db_session.get(Vehiculo, item.id).kilometraje_actual == 125
    null_km = vehicle(db_session, placa="ORD-NULL", kilometraje=None)
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(null_km, numero_orden="LOG-NULL", kilometraje_orden=5)).status_code == 201
    db_session.rollback(); db_session.expire_all(); assert db_session.get(Vehiculo, null_km.id).kilometraje_actual == 5


def test_order_validates_preventives_provider_and_required_content(client, db_session):
    item = vehicle(db_session); cat = catalog(db_session); auth = headers(client)
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, preventivo_ids=[999], descripcion_correctivo=None)).status_code == 422
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, preventivo_ids=[cat.id, cat.id], descripcion_correctivo=None)).status_code == 422
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, proveedor_id=999)).status_code == 404
    inactive_provider = Proveedor(razon_social="Proveedor inactivo", activo=False); db_session.add(inactive_provider); db_session.commit(); db_session.refresh(inactive_provider)
    response = client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, proveedor_id=inactive_provider.id))
    assert response.status_code == 422 and response.json()["detail"] == "El proveedor seleccionado está inactivo"
    assert client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, preventivo_ids=[], descripcion_correctivo=" ")).status_code == 422


def test_order_persists_preventive_corrective_and_operational_fields(client, db_session):
    item = vehicle(db_session); first = catalog(db_session); second = catalog(db_session, component="CAT-002", tarea="Cambio de filtro")
    provider = Proveedor(razon_social="Taller Prueba", activo=True); db_session.add(provider); db_session.commit(); db_session.refresh(provider)
    response = client.post("/api/v1/ordenes-servicio", headers=headers(client), json=payload(item, preventivo_ids=[first.id, second.id], proveedor_id=provider.id))
    assert response.status_code == 201
    body = response.json()
    assert body["estado"] == "ABIERTA" and body["estado_archivo"] == "PENDIENTE"
    assert body["es_historico"] is False and body["fuente_origen"] == "OPERATIVO"
    assert body["monto"] is None and body["dias_parada"] is None
    assert body["fecha"] == date.today().isoformat()
    assert {entry["id"] for entry in body["preventivos"]} == {first.id, second.id}
    db_session.rollback(); order = db_session.get(OrdenServicio, body["id"])
    assert order.descripcion_correctivo == "Reparación de freno"
    assert "Cambio de aceite" in order.descripcion and "Reparación de freno" in order.descripcion
    assert len(db_session.scalars(select(OrdenServicioPreventivo).where(OrdenServicioPreventivo.orden_servicio_id == order.id)).all()) == 2
    assert client.get(f"/api/v1/ordenes-servicio/{order.id}", headers=headers(client, "MECANICO")).status_code == 200


def test_order_supports_preventive_only_and_corrective_only(client, db_session):
    item = vehicle(db_session); cat = catalog(db_session); auth = headers(client)
    preventive = client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, preventivo_ids=[cat.id], descripcion_correctivo=None))
    corrective = client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(item, numero_orden="LOG-COR", preventivo_ids=[], descripcion_correctivo="Soldadura"))
    assert preventive.status_code == corrective.status_code == 201
    assert "Cambio de aceite" in preventive.json()["descripcion"]
    assert corrective.json()["descripcion"] == "Correctivo: Soldadura"


def test_auxiliary_endpoints_and_historical_order_remain_unchanged(client, db_session):
    active = vehicle(db_session); vehicle(db_session, placa="ORD-INACT", estado="INACTIVO")
    cat = catalog(db_session); provider = Proveedor(razon_social="Proveedor activo", activo=True, es_historico=True, fuente_origen="Control_Flota_DIRESA")
    historical = OrdenServicio(numero_orden="SOAT1", id_orden_origen="SOAT1", vehiculo_id=active.id, fecha=date(2025, 8, 1), descripcion="SOAT", monto=38, estado="Archivado", es_historico=True, fuente_origen="Control_Flota_DIRESA")
    db_session.add_all([provider, historical]); db_session.commit(); db_session.refresh(historical)
    auth = headers(client)
    assert [v["id"] for v in client.get("/api/v1/ordenes-servicio/vehicles", headers=auth).json()] == [active.id]
    assert client.get("/api/v1/ordenes-servicio/maintenance-catalog?search=aceite", headers=auth).json()[0]["id"] == cat.id
    assert client.get("/api/v1/ordenes-servicio/providers", headers=auth).status_code == 200
    before = (historical.id, historical.id_orden_origen, historical.numero_orden, historical.es_historico, historical.fuente_origen, historical.estado)
    client.post("/api/v1/ordenes-servicio", headers=auth, json=payload(active, numero_orden="LOG-NUEVA"))
    db_session.expire_all(); current = db_session.get(OrdenServicio, historical.id)
    assert before == (current.id, current.id_orden_origen, current.numero_orden, current.es_historico, current.fuente_origen, current.estado)


def test_duplicate_order_error_detection_is_specific():
    duplicate = IntegrityError("insert", {}, MySQLIntegrityError(1062, "Duplicate entry for key 'numero_orden'"))
    unexpected = IntegrityError("insert", {}, MySQLIntegrityError(1452, "Cannot add foreign key"))
    assert is_duplicate_order_error(duplicate)
    assert not is_duplicate_order_error(unexpected)


def test_preventive_relationship_has_no_delete_cascade():
    assert "delete" not in OrdenServicio.preventivos.property.cascade
    assert OrdenServicioPreventivo.orden_servicio.property.mapper.class_ is OrdenServicio
    assert OrdenServicioPreventivo.catalogo.property.mapper.class_ is CatalogoMantenimientoOrigen
