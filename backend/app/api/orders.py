from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import CatalogoMantenimientoOrigen, OrdenServicio, OrdenServicioPreventivo, Proveedor, Usuario, Vehiculo
from app.schemas.order import MaintenanceCatalogRead, OrderCreate, OrderPreventiveRead, OrderRead, OrderVehicleRead, ProviderRead

router = APIRouter(prefix="/api/v1/ordenes-servicio", tags=["ordenes-servicio"])
ALLOWED_ROLES = {"ADMINISTRADOR", "MECANICO"}
# Perú does not observe daylight saving time; a fixed offset also works on Windows
# environments where the IANA tzdata package is not installed.
LIMA = timezone(timedelta(hours=-5), name="America/Lima")


def operational_user(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol.codigo not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar órdenes de servicio")
    return user


def read_order(order: OrdenServicio) -> OrderRead:
    return OrderRead(
        id=order.id,
        numero_orden=order.numero_orden,
        vehiculo_id=order.vehiculo_id,
        proveedor_id=order.proveedor_id,
        fecha=order.fecha,
        descripcion=order.descripcion,
        descripcion_correctivo=order.descripcion_correctivo,
        kilometraje_orden=order.kilometraje_orden,
        dias_parada=order.dias_parada,
        monto=order.monto,
        estado=order.estado,
        estado_archivo=order.estado_archivo,
        es_historico=order.es_historico,
        fuente_origen=order.fuente_origen,
        preventivos=[OrderPreventiveRead(id=item.catalogo.id, id_componente_origen=item.catalogo.id_componente_origen, tarea=item.catalogo.tarea) for item in order.preventivos],
    )


def is_duplicate_order_error(error: IntegrityError) -> bool:
    """Recognize only the database unique violation for numero_orden.

    The pre-check provides a clear ordinary response; this check preserves the
    same response for the race protected by the database UNIQUE constraint.
    """
    original = error.orig
    code = getattr(original, "args", [None])[0]
    return code == 1062 and "numero_orden" in str(original).lower()


@router.get("/vehicles", response_model=list[OrderVehicleRead])
def available_vehicles(db: Session = Depends(get_db), _: Usuario = Depends(operational_user)) -> list[Vehiculo]:
    return list(db.scalars(select(Vehiculo).where(Vehiculo.estado != "INACTIVO").order_by(Vehiculo.placa)))


@router.get("/maintenance-catalog", response_model=list[MaintenanceCatalogRead])
def maintenance_catalog(search: str | None = Query(default=None, max_length=200), db: Session = Depends(get_db), _: Usuario = Depends(operational_user)) -> list[CatalogoMantenimientoOrigen]:
    query = select(CatalogoMantenimientoOrigen)
    if search and search.strip():
        query = query.where(CatalogoMantenimientoOrigen.tarea.ilike(f"%{search.strip()}%"))
    return list(db.scalars(query.order_by(CatalogoMantenimientoOrigen.tarea)))


@router.get("/providers", response_model=list[ProviderRead])
def providers(db: Session = Depends(get_db), _: Usuario = Depends(operational_user)) -> list[Proveedor]:
    return list(db.scalars(select(Proveedor).where(Proveedor.activo.is_(True)).order_by(Proveedor.razon_social)))


@router.post("", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), _: Usuario = Depends(operational_user)) -> OrderRead:
    vehicle = db.scalar(select(Vehiculo).where(Vehiculo.id == payload.vehiculo_id).with_for_update())
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    if vehicle.estado == "INACTIVO":
        raise HTTPException(status_code=422, detail="No se puede crear una orden para un vehículo inactivo")
    if vehicle.kilometraje_actual is not None and payload.kilometraje_orden < vehicle.kilometraje_actual:
        raise HTTPException(status_code=422, detail="El kilometraje de la orden no puede ser menor al kilometraje actual")

    catalogs = list(db.scalars(select(CatalogoMantenimientoOrigen).where(CatalogoMantenimientoOrigen.id.in_(payload.preventivo_ids)).order_by(CatalogoMantenimientoOrigen.id))) if payload.preventivo_ids else []
    if len(catalogs) != len(payload.preventivo_ids):
        raise HTTPException(status_code=422, detail="Uno o más preventivos no existen")
    if payload.proveedor_id is not None:
        provider = db.get(Proveedor, payload.proveedor_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        if not provider.activo:
            raise HTTPException(status_code=422, detail="El proveedor seleccionado está inactivo")
    if db.scalar(select(OrdenServicio.id).where(OrdenServicio.numero_orden == payload.numero_orden)) is not None:
        raise HTTPException(status_code=409, detail="El número de orden ya está registrado")

    parts = []
    if catalogs:
        parts.append("Preventivo: " + "; ".join(item.tarea for item in catalogs))
    if payload.descripcion_correctivo:
        parts.append("Correctivo: " + payload.descripcion_correctivo)
    order = OrdenServicio(
        numero_orden=payload.numero_orden,
        vehiculo_id=vehicle.id,
        proveedor_id=payload.proveedor_id,
        fecha=datetime.now(LIMA).date(),
        descripcion=" | ".join(parts),
        descripcion_correctivo=payload.descripcion_correctivo,
        kilometraje_orden=payload.kilometraje_orden,
        dias_parada=None,
        monto=None,
        estado="ABIERTA",
        estado_archivo=payload.estado_archivo,
        es_historico=False,
        fuente_origen="OPERATIVO",
    )
    order.preventivos = [OrdenServicioPreventivo(catalogo=item) for item in catalogs]
    if vehicle.kilometraje_actual is None or payload.kilometraje_orden > vehicle.kilometraje_actual:
        vehicle.kilometraje_actual = payload.kilometraje_orden
    db.add(order)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if is_duplicate_order_error(error):
            raise HTTPException(status_code=409, detail="El número de orden ya está registrado")
        raise HTTPException(status_code=500, detail="No fue posible guardar la orden de servicio")
    loaded = db.scalar(select(OrdenServicio).options(selectinload(OrdenServicio.preventivos).selectinload(OrdenServicioPreventivo.catalogo)).where(OrdenServicio.id == order.id))
    return read_order(loaded)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db), _: Usuario = Depends(operational_user)) -> OrderRead:
    order = db.scalar(select(OrdenServicio).options(selectinload(OrdenServicio.preventivos).selectinload(OrdenServicioPreventivo.catalogo)).where(OrdenServicio.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Orden de servicio no encontrada")
    return read_order(order)
