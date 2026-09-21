from datetime import date
from pydantic import BaseModel, Field, field_validator

VALID_STATES = {"OPERATIVO", "MANTENIMIENTO", "INACTIVO"}

class VehicleBase(BaseModel):
    placa: str | None = Field(default=None, max_length=20)
    marca: str | None = Field(default=None, max_length=80)
    modelo: str | None = Field(default=None, max_length=80)
    anio: int | None = Field(default=None, ge=1900, le=2100)
    tipo: str | None = Field(default=None, max_length=50)
    kilometraje_actual: int | None = Field(default=None, ge=0)
    estado: str | None = None
    soat_vencimiento: date | None = None
    revision_tecnica_vencimiento: date | None = None
    observaciones: str | None = None

    @field_validator("placa")
    @classmethod
    def normalize_plate(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("estado")
    @classmethod
    def validate_state(cls, value: str | None) -> str | None:
        if value is not None and value.upper() not in VALID_STATES:
            raise ValueError("Estado inválido")
        return value.upper() if value else value

class VehicleCreate(VehicleBase):
    placa: str
    marca: str
    modelo: str
    anio: int
    tipo: str
    kilometraje_actual: int = Field(default=0, ge=0)
    estado: str = "OPERATIVO"

class VehicleUpdate(VehicleBase): pass

class VehicleRead(BaseModel):
    id: int; placa: str; marca: str; modelo: str; anio: int | None; tipo: str; kilometraje_actual: int; estado: str
    soat_vencimiento: date | None; revision_tecnica_vencimiento: date | None; observaciones: str | None
    model_config = {"from_attributes": True}

class VehicleListResponse(BaseModel):
    items: list[VehicleRead]; total: int; page: int; page_size: int
