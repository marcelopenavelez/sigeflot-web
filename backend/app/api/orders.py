from datetime import date, datetime, timedelta, timezone
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import CatalogoMantenimientoOrigen, OrdenServicio, OrdenServicioAuditoria, OrdenServicioPreventivo, Proveedor, Usuario, Vehiculo
from app.schemas.order import (MaintenanceCatalogRead, OrderCreate, OrderDetailRead, OrderListItemRead,
    OrderListResponse, OrderPreventiveDetailRead, OrderPreventiveRead, OrderRead, OrderVehicleRead, ProviderRead, OrderUpdate, OrderArchiveUpdate, OrderAuditRead)

router = APIRouter(prefix="/api/v1/ordenes-servicio", tags=["ordenes-servicio"])
ALLOWED_ROLES = {"ADMINISTRADOR", "MECANICO"}
READ_ROLES = {"ADMINISTRADOR", "MECANICO", "CONSULTA"}
# Perú does not observe daylight saving time; a fixed offset also works on Windows
# environments where the IANA tzdata package is not installed.
LIMA = timezone(timedelta(hours=-5), name="America/Lima")


def operational_user(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol.codigo not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="No tiene permisos para gestionar órdenes de servicio")
    return user


def order_reader(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol.codigo not in READ_ROLES:
        raise HTTPException(status_code=403, detail="No tiene permisos para consultar órdenes de servicio")
    return user

def mutable_order(db: Session, order_id: int) -> OrdenServicio:
    order = db.scalar(select(OrdenServicio).options(selectinload(OrdenServicio.preventivos)).where(OrdenServicio.id == order_id).with_for_update())
    if order is None: raise HTTPException(status_code=404, detail="Orden de servicio no encontrada")
    if order.es_historico: raise HTTPException(status_code=409, detail="La orden histórica es solo lectura")
    return order

def audit(db: Session, order: OrdenServicio, user: Usuario, action: str, changes: dict) -> None:
    db.add(OrdenServicioAuditoria(orden_servicio_id=order.id, usuario_id=user.id, accion=action, fecha_hora=datetime.now(LIMA), cambios=jsonable_encoder(changes)))


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


def order_filters(search: str | None, placa: str | None, estado: str | None, estado_archivo: str | None,
                  es_historico: bool | None, fecha_desde: date | None, fecha_hasta: date | None):
    conditions = []
    if search and search.strip():
        conditions.append(OrdenServicio.numero_orden.ilike(f"%{search.strip()}%"))
    if placa and placa.strip():
        conditions.append(Vehiculo.placa.ilike(f"%{placa.strip()}%"))
    if estado and estado.strip():
        conditions.append(OrdenServicio.estado == estado.strip())
    if estado_archivo and estado_archivo.strip():
        conditions.append(OrdenServicio.estado_archivo == estado_archivo.strip())
    if es_historico is not None:
        conditions.append(OrdenServicio.es_historico.is_(es_historico))
    if fecha_desde is not None:
        conditions.append(OrdenServicio.fecha >= fecha_desde)
    if fecha_hasta is not None:
        conditions.append(OrdenServicio.fecha <= fecha_hasta)
    return conditions


@router.get("", response_model=OrderListResponse)
def list_orders(search: str | None = Query(default=None, max_length=100), placa: str | None = Query(default=None, max_length=20),
                estado: str | None = Query(default=None, max_length=20), estado_archivo: str | None = Query(default=None, max_length=20),
                es_historico: bool | None = None, fecha_desde: date | None = None, fecha_hasta: date | None = None,
                page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
                db: Session = Depends(get_db), _: Usuario = Depends(order_reader)) -> OrderListResponse:
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(status_code=422, detail="La fecha desde no puede ser posterior a la fecha hasta")
    conditions = order_filters(search, placa, estado, estado_archivo, es_historico, fecha_desde, fecha_hasta)
    query = select(OrdenServicio, Vehiculo.placa, Proveedor.razon_social).outerjoin(Vehiculo, OrdenServicio.vehiculo_id == Vehiculo.id).outerjoin(Proveedor, OrdenServicio.proveedor_id == Proveedor.id)
    total = db.scalar(select(func.count()).select_from(OrdenServicio).outerjoin(Vehiculo, OrdenServicio.vehiculo_id == Vehiculo.id).outerjoin(Proveedor, OrdenServicio.proveedor_id == Proveedor.id).where(*conditions)) or 0
    rows = db.execute(query.where(*conditions).order_by(OrdenServicio.fecha.desc(), OrdenServicio.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return OrderListResponse(items=[OrderListItemRead(id=order.id, numero_orden=order.numero_orden, id_orden_origen=order.id_orden_origen, fecha=order.fecha, placa=plate, kilometraje_orden=order.kilometraje_orden, proveedor=provider, estado=order.estado, estado_archivo=order.estado_archivo, es_historico=order.es_historico, monto=order.monto, dias_parada=order.dias_parada) for order, plate, provider in rows], page=page, page_size=page_size, total=total, pages=ceil(total / page_size) if total else 0)


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


@router.get("/{order_id}", response_model=OrderDetailRead)
def get_order(order_id: int, db: Session = Depends(get_db), _: Usuario = Depends(order_reader)) -> OrderDetailRead:
    order = db.scalar(select(OrdenServicio).options(selectinload(OrdenServicio.vehiculo), selectinload(OrdenServicio.proveedor), selectinload(OrdenServicio.preventivos).selectinload(OrdenServicioPreventivo.catalogo)).where(OrdenServicio.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Orden de servicio no encontrada")
    return OrderDetailRead(**read_order(order).model_dump(exclude={"preventivos"}), id_orden_origen=order.id_orden_origen,
        placa=order.vehiculo.placa if order.vehiculo else None,
        proveedor=order.proveedor.razon_social if order.proveedor else None,
        preventivos=[OrderPreventiveDetailRead(id=item.catalogo.id, id_componente_origen=item.catalogo.id_componente_origen,
            tarea=item.catalogo.tarea, prioridad=item.catalogo.prioridad) for item in order.preventivos])

@router.patch("/{order_id}", response_model=OrderRead)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db), user: Usuario = Depends(operational_user)):
    order = mutable_order(db, order_id)
    if order.estado != "ABIERTA": raise HTTPException(status_code=409, detail="La orden cerrada no puede editarse")
    data = payload.model_dump(exclude_unset=True); before = {}
    if "proveedor_id" in data and data["proveedor_id"] is not None:
        provider = db.get(Proveedor, data["proveedor_id"])
        if provider is None: raise HTTPException(status_code=422, detail="Proveedor no encontrado")
        if not provider.activo: raise HTTPException(status_code=422, detail="El proveedor seleccionado está inactivo")
    if "preventivo_ids" in data:
        ids = data["preventivo_ids"] or []
        if len(ids) != len(set(ids)): raise HTTPException(status_code=422, detail="No se permiten preventivos duplicados")
        catalogs=list(db.scalars(select(CatalogoMantenimientoOrigen).where(CatalogoMantenimientoOrigen.id.in_(ids)))) if ids else []
        if len(catalogs) != len(ids): raise HTTPException(status_code=422, detail="Uno o más preventivos no existen")
        if not catalogs and not (data.get("descripcion_correctivo", order.descripcion_correctivo) or "").strip(): raise HTTPException(status_code=422, detail="Seleccione un preventivo o ingrese una descripción correctiva")
        before["preventivo_ids"]={"antes":[x.catalogo_mantenimiento_origen_id for x in order.preventivos],"despues":ids}; order.preventivos=[OrdenServicioPreventivo(catalogo=x) for x in catalogs]
    for field in ("kilometraje_orden","proveedor_id","descripcion_correctivo","monto","dias_parada"):
        if field in data and getattr(order,field)!=data[field]: before[field]={"antes":getattr(order,field),"despues":data[field]}; setattr(order,field,data[field])
    if order.kilometraje_orden is not None:
        vehicle=db.get(Vehiculo,order.vehiculo_id)
        if vehicle and (vehicle.kilometraje_actual is None or order.kilometraje_orden>vehicle.kilometraje_actual): vehicle.kilometraje_actual=order.kilometraje_orden
    if not order.preventivos and not (order.descripcion_correctivo or "").strip(): raise HTTPException(status_code=422, detail="La orden requiere mantenimiento")
    if before: audit(db,order,user,"EDITADA",before)
    db.commit(); db.refresh(order); return read_order(order)

@router.post("/{order_id}/cerrar", response_model=OrderRead)
def close_order(order_id:int, db:Session=Depends(get_db), user:Usuario=Depends(operational_user)):
    order=mutable_order(db,order_id)
    if order.estado != "ABIERTA": raise HTTPException(status_code=409, detail="La orden ya está cerrada")
    if not order.preventivos and not (order.descripcion_correctivo or "").strip(): raise HTTPException(status_code=422, detail="La orden requiere mantenimiento")
    order.estado="CERRADA"; order.fecha_hora_cierre=datetime.now(LIMA); order.cerrado_por_usuario_id=user.id; audit(db,order,user,"CERRADA",{}); db.commit(); db.refresh(order); return read_order(order)

@router.patch("/{order_id}/archivo", response_model=OrderRead)
def archive_order(order_id:int,payload:OrderArchiveUpdate,db:Session=Depends(get_db),user:Usuario=Depends(operational_user)):
    order=mutable_order(db,order_id); changes={"estado_archivo":{"antes":order.estado_archivo,"despues":payload.estado_archivo}}; order.estado_archivo=payload.estado_archivo; audit(db,order,user,"ESTADO_ARCHIVO_CAMBIADO",changes); db.commit(); db.refresh(order); return read_order(order)

@router.get("/{order_id}/auditoria", response_model=list[OrderAuditRead])
def order_audit(order_id:int,db:Session=Depends(get_db),_:Usuario=Depends(order_reader)):
    if db.get(OrdenServicio,order_id) is None: raise HTTPException(status_code=404,detail="Orden de servicio no encontrada")
    rows=db.scalars(select(OrdenServicioAuditoria).options(selectinload(OrdenServicioAuditoria.usuario)).where(OrdenServicioAuditoria.orden_servicio_id==order_id).order_by(OrdenServicioAuditoria.fecha_hora.desc())).all()
    return [OrderAuditRead(accion=x.accion,fecha_hora=x.fecha_hora,usuario=f"{x.usuario.nombres} {x.usuario.apellidos}",cambios=x.cambios) for x in rows]
