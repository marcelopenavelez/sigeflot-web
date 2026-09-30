from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook
from sqlalchemy import func, select

from app.models import CatalogoMantenimientoBIOrigen, CatalogoMantenimientoOrigen, Mantenimiento, OrdenServicio, Proveedor, Salida, Vehiculo
from app.scripts.import_official_data import SOURCE, data, load, n, optional_money, t


WORKBOOK = Path(__file__).resolve().parents[2] / "Control_Flota_DIRESA.xlsx"


def test_order_import_preserves_official_fields_and_is_idempotent(db_session):
    if not WORKBOOK.exists():
        pytest.skip(
            "Control_Flota_DIRESA.xlsx is a local official-data source and is intentionally not versioned"
        )

    workbook = load_workbook(WORKBOOK, read_only=True, data_only=True)
    source_orders = data(workbook, "Orden")

    first = load(workbook, db_session, True)
    db_session.commit()
    assert first["service-orders"]["CREATED"] == len(source_orders) == 18
    assert db_session.scalar(select(func.count()).select_from(Vehiculo)) == 48
    assert db_session.scalar(select(func.count()).select_from(Mantenimiento)) == 231
    assert db_session.scalar(select(func.count()).select_from(CatalogoMantenimientoOrigen)) == 80
    assert db_session.scalar(select(func.count()).select_from(CatalogoMantenimientoBIOrigen)) == 297
    assert db_session.scalar(select(func.count()).select_from(Proveedor)) > 0
    assert db_session.scalar(select(func.count()).select_from(Salida)) > 0

    imported = {item.id_orden_origen: item for item in db_session.scalars(select(OrdenServicio)).all()}
    for row in source_orders:
        identifier = t(row["ID_Orden"])
        order = imported[identifier]
        assert order.numero_orden == identifier
        assert order.kilometraje_orden == n(row["Kilometraje"])
        assert order.dias_parada == n(row["Dias_de_parada"])
        assert order.descripcion_correctivo == t(row["Descripcion_Correctivo"])
        assert order.estado_archivo == t(row["Estado_Archivo"])
        assert order.estado == "HISTORICO"
        assert order.es_historico is True
        assert order.fuente_origen == SOURCE
        expected_amount = optional_money(row["Costo_Total_Orden"])
        assert order.monto == expected_amount

    snapshot = [(item.id, item.id_orden_origen, item.numero_orden, item.kilometraje_orden, item.dias_parada, item.descripcion_correctivo, item.estado_archivo, item.estado, item.monto) for item in imported.values()]
    second = load(workbook, db_session, True)
    db_session.commit()
    assert second["service-orders"]["CREATED"] == 0
    assert db_session.scalar(select(func.count()).select_from(OrdenServicio)) == 18
    after = [(item.id, item.id_orden_origen, item.numero_orden, item.kilometraje_orden, item.dias_parada, item.descripcion_correctivo, item.estado_archivo, item.estado, item.monto) for item in db_session.scalars(select(OrdenServicio)).all()]
    assert sorted(snapshot) == sorted(after)
    maintenance_kilometrajes = list(db_session.scalars(select(Mantenimiento.kilometraje)))
    assert None in maintenance_kilometrajes
    assert 0 in maintenance_kilometrajes
    assert any(value is not None and value > 0 for value in maintenance_kilometrajes)
    assert all(item.es_historico and item.fuente_origen == SOURCE for item in db_session.scalars(select(Mantenimiento)).all())


def test_optional_money_does_not_invent_a_cost():
    assert optional_money(None) is None
    assert optional_money(0) == Decimal("0")
