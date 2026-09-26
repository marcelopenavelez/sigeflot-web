from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import Conductor, Salida, Usuario, Vehiculo
from app.schemas.exit import ExitCreate, ExitRead, ExitVehicleOption

router = APIRouter(prefix="/api/v1/salidas", tags=["salidas"])
ALLOWED_ROLES = {"ADMINISTRADOR", "MECANICO", "CHOFER"}


def operational_user(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol.codigo not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="No tiene permisos para registrar salidas")
    return user


@router.get("/vehicles", response_model=list[ExitVehicleOption])
def available_vehicles(
    db: Session = Depends(get_db), _: Usuario = Depends(operational_user)
) -> list[Vehiculo]:
    """Return only the fields required by the operational exit selector."""
    open_exit = select(Salida.vehiculo_id).where(Salida.estado == "ABIERTA")
    return list(db.scalars(
        select(Vehiculo)
        .where(Vehiculo.estado == "OPERATIVO", Vehiculo.id.not_in(open_exit))
        .order_by(Vehiculo.placa)
    ))


@router.post("", response_model=ExitRead, status_code=201)
def create_exit(
    payload: ExitCreate, db: Session = Depends(get_db), user: Usuario = Depends(operational_user)
) -> Salida:
    normalized_email = user.email.strip().lower()
    conductores = list(db.scalars(
        select(Conductor).where(
            Conductor.activo.is_(True),
            func.lower(Conductor.email) == normalized_email,
        )
    ))
    if not conductores:
        raise HTTPException(status_code=422, detail="El usuario autenticado no está asociado a un conductor activo")
    if len(conductores) > 1:
        raise HTTPException(status_code=409, detail="Existe más de un conductor activo asociado al correo del usuario")
    conductor = conductores[0]

    # This lock serializes operational creates for the selected vehicle.
    vehicle = db.scalar(select(Vehiculo).where(Vehiculo.id == payload.vehiculo_id).with_for_update())
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    if vehicle.estado != "OPERATIVO":
        raise HTTPException(status_code=422, detail="El vehículo no está operativo")
    if vehicle.kilometraje_actual is None:
        raise HTTPException(status_code=422, detail="El vehículo no tiene kilometraje actual registrado")
    if payload.kilometraje_salida < vehicle.kilometraje_actual:
        raise HTTPException(status_code=422, detail="El kilometraje de salida no puede ser menor al kilometraje actual")
    if db.scalar(select(Salida.id).where(Salida.vehiculo_id == vehicle.id, Salida.estado == "ABIERTA")) is not None:
        raise HTTPException(status_code=409, detail="El vehículo ya tiene una salida abierta")

    salida = Salida(
        vehiculo_id=vehicle.id,
        conductor_id=conductor.id,
        fecha_hora_salida=datetime.now(timezone.utc),
        kilometraje_salida=payload.kilometraje_salida,
        observaciones=payload.observaciones or None,
        estado="ABIERTA",
        es_historico=False,
        fuente_origen="OPERATIVO",
    )
    vehicle.kilometraje_actual = payload.kilometraje_salida
    db.add(salida)
    db.commit()
    db.refresh(salida)
    return salida
