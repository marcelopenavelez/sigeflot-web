from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.api.users import admin_required
from app.core.database import get_db
from app.models import Usuario, Vehiculo
from app.schemas.vehicle import VehicleCreate, VehicleListResponse, VehicleRead, VehicleUpdate

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])

def require_roles(*roles: str):
    def checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.rol.codigo not in roles: raise HTTPException(status_code=403, detail="Permisos insuficientes")
        return user
    return checker

@router.post("", response_model=VehicleRead, status_code=201)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db), _: Usuario = Depends(admin_required)):
    vehicle = Vehiculo(**payload.model_dump()); db.add(vehicle)
    try: db.commit(); db.refresh(vehicle)
    except IntegrityError: db.rollback(); raise HTTPException(status_code=409, detail="La placa ya está registrada")
    return vehicle

@router.get("", response_model=VehicleListResponse)
def list_vehicles(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, estado: str | None = None, tipo: str | None = None, db: Session = Depends(get_db), _: Usuario = Depends(require_roles("ADMINISTRADOR", "MECANICO", "CHOFER", "CONSULTA"))):
    query = select(Vehiculo)
    if search: query = query.where(or_(Vehiculo.placa.ilike(f"%{search}%"), Vehiculo.marca.ilike(f"%{search}%"), Vehiculo.modelo.ilike(f"%{search}%")))
    if estado: query = query.where(Vehiculo.estado == estado.upper())
    if tipo: query = query.where(Vehiculo.tipo == tipo.upper())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(Vehiculo.id).offset((page - 1) * page_size).limit(page_size)).all()
    return VehicleListResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    vehicle = db.get(Vehiculo, vehicle_id)
    if vehicle is None: raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return vehicle

@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(vehicle_id: int, payload: VehicleUpdate, db: Session = Depends(get_db), _: Usuario = Depends(require_roles("ADMINISTRADOR", "MECANICO"))):
    vehicle = db.get(Vehiculo, vehicle_id)
    if vehicle is None: raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    changes = payload.model_dump(exclude_unset=True)
    if "kilometraje_actual" in changes and changes["kilometraje_actual"] < vehicle.kilometraje_actual: raise HTTPException(status_code=422, detail="El kilometraje no puede disminuir")
    for field, value in changes.items(): setattr(vehicle, field, value)
    try: db.commit(); db.refresh(vehicle)
    except IntegrityError: db.rollback(); raise HTTPException(status_code=409, detail="La placa ya está registrada")
    return vehicle

@router.delete("/{vehicle_id}", status_code=204)
def deactivate_vehicle(vehicle_id: int, db: Session = Depends(get_db), _: Usuario = Depends(admin_required)):
    vehicle = db.get(Vehiculo, vehicle_id)
    if vehicle is None: raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    vehicle.estado = "INACTIVO"; db.commit()
    return Response(status_code=204)
