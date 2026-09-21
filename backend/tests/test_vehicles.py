from .conftest import token


def headers_for(client, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(client, f'{role.lower()}@example.com')}"}


def vehicle_payload(**changes):
    payload = {"placa": " eac-782 ", "marca": "Toyota", "modelo": "Hilux", "anio": 2022, "tipo": "CAMIONETA", "kilometraje_actual": 45000, "estado": "OPERATIVO"}
    payload.update(changes)
    return payload


def create_vehicle(client, admin_headers, **changes):
    response = client.post("/api/v1/vehicles", json=vehicle_payload(**changes), headers=admin_headers)
    assert response.status_code == 201
    return response.json()


def test_admin_creates_and_normalizes_plate(client, admin_headers):
    vehicle = create_vehicle(client, admin_headers)
    assert vehicle["placa"] == "EAC-782"


def test_non_admin_cannot_create(client):
    for role in ("CHOFER", "CONSULTA"):
        assert client.post("/api/v1/vehicles", json=vehicle_payload(), headers=headers_for(client, role)).status_code == 403


def test_duplicate_and_invalid_kilometraje(client, admin_headers):
    create_vehicle(client, admin_headers)
    assert client.post("/api/v1/vehicles", json=vehicle_payload(placa="eac-782"), headers=admin_headers).status_code == 409
    assert client.post("/api/v1/vehicles", json=vehicle_payload(placa="ABC-123", kilometraje_actual=-1), headers=admin_headers).status_code == 422


def test_list_pagination_search_and_filters(client, admin_headers):
    create_vehicle(client, admin_headers)
    create_vehicle(client, admin_headers, placa="ABC-123", marca="Nissan", modelo="Frontier", estado="MANTENIMIENTO", tipo="CAMIONETA")
    headers = headers_for(client, "CONSULTA")
    listed = client.get("/api/v1/vehicles?page=1&page_size=1", headers=headers).json()
    assert listed["total"] == 2 and len(listed["items"]) == 1
    assert client.get("/api/v1/vehicles?search=EAC", headers=headers).json()["total"] == 1
    assert client.get("/api/v1/vehicles?estado=MANTENIMIENTO", headers=headers).json()["total"] == 1
    assert client.get("/api/v1/vehicles?tipo=CAMIONETA", headers=headers).json()["total"] == 2


def test_detail_and_not_found(client, admin_headers):
    vehicle = create_vehicle(client, admin_headers)
    headers = headers_for(client, "CHOFER")
    assert client.get(f"/api/v1/vehicles/{vehicle['id']}", headers=headers).status_code == 200
    assert client.get("/api/v1/vehicles/99999", headers=headers).status_code == 404


def test_update_roles_and_kilometraje_rule(client, admin_headers):
    vehicle = create_vehicle(client, admin_headers)
    assert client.patch(f"/api/v1/vehicles/{vehicle['id']}", json={"marca":"Ford"}, headers=admin_headers).status_code == 200
    assert client.patch(f"/api/v1/vehicles/{vehicle['id']}", json={"modelo":"Ranger"}, headers=headers_for(client, "MECANICO")).status_code == 200
    assert client.patch(f"/api/v1/vehicles/{vehicle['id']}", json={"marca":"X"}, headers=headers_for(client, "CHOFER")).status_code == 403
    assert client.patch(f"/api/v1/vehicles/{vehicle['id']}", json={"kilometraje_actual":44000}, headers=admin_headers).status_code == 422


def test_logical_delete_and_persistence(client, admin_headers):
    vehicle = create_vehicle(client, admin_headers)
    assert client.delete(f"/api/v1/vehicles/{vehicle['id']}", headers=headers_for(client, "MECANICO")).status_code == 403
    assert client.delete(f"/api/v1/vehicles/{vehicle['id']}", headers=admin_headers).status_code == 204
    stored = client.get(f"/api/v1/vehicles/{vehicle['id']}", headers=headers_for(client, "CONSULTA"))
    assert stored.status_code == 200 and stored.json()["estado"] == "INACTIVO"
