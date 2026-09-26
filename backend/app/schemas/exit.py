from datetime import datetime

from pydantic import BaseModel, Field


class ExitCreate(BaseModel):
    vehiculo_id: int = Field(gt=0)
    kilometraje_salida: int = Field(ge=0)
    observaciones: str | None = Field(default=None, max_length=2000)


class ExitVehicleOption(BaseModel):
    id: int
    placa: str
    marca: str | None
    modelo: str | None
    kilometraje_actual: int | None
    estado: str

    model_config = {"from_attributes": True}


class ExitRead(BaseModel):
    id: int
    vehiculo_id: int
    conductor_id: int
    fecha_hora_salida: datetime
    kilometraje_salida: int
    observaciones: str | None
    estado: str
    es_historico: bool
    fuente_origen: str | None

    model_config = {"from_attributes": True}
