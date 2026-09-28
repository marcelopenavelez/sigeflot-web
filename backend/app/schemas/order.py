from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


ARCHIVE_STATES = {"PENDIENTE", "ARCHIVADO"}


class OrderCreate(BaseModel):
    numero_orden: str = Field(min_length=1, max_length=40)
    vehiculo_id: int = Field(gt=0)
    kilometraje_orden: int = Field(ge=0)
    preventivo_ids: list[int] = Field(default_factory=list)
    descripcion_correctivo: str | None = Field(default=None, max_length=5000)
    proveedor_id: int | None = Field(default=None, gt=0)
    estado_archivo: str

    @field_validator("numero_orden")
    @classmethod
    def normalize_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El número de orden es obligatorio")
        return value

    @field_validator("descripcion_correctivo")
    @classmethod
    def normalize_corrective(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @field_validator("estado_archivo")
    @classmethod
    def validate_archive_state(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in ARCHIVE_STATES:
            raise ValueError("Estado de archivo inválido")
        return value

    @model_validator(mode="after")
    def validate_content(self) -> "OrderCreate":
        if len(set(self.preventivo_ids)) != len(self.preventivo_ids):
            raise ValueError("No se permiten preventivos duplicados")
        if not self.preventivo_ids and not self.descripcion_correctivo:
            raise ValueError("Seleccione un preventivo o ingrese una descripción correctiva")
        return self


class OrderPreventiveRead(BaseModel):
    id: int
    id_componente_origen: str
    tarea: str


class OrderPreventiveDetailRead(OrderPreventiveRead):
    prioridad: str | None


class OrderRead(BaseModel):
    id: int
    numero_orden: str
    vehiculo_id: int | None
    proveedor_id: int | None
    fecha: date | None
    descripcion: str
    descripcion_correctivo: str | None
    kilometraje_orden: int | None
    dias_parada: int | None
    monto: Decimal | None
    estado: str
    estado_archivo: str | None
    es_historico: bool
    fuente_origen: str | None
    preventivos: list[OrderPreventiveRead]


class OrderDetailRead(OrderRead):
    id_orden_origen: str | None
    placa: str | None
    proveedor: str | None
    preventivos: list[OrderPreventiveDetailRead]


class OrderListItemRead(BaseModel):
    id: int
    numero_orden: str
    id_orden_origen: str | None
    fecha: date | None
    placa: str | None
    kilometraje_orden: int | None
    proveedor: str | None
    estado: str
    estado_archivo: str | None
    es_historico: bool
    monto: Decimal | None
    dias_parada: int | None


class OrderListResponse(BaseModel):
    items: list[OrderListItemRead]
    page: int
    page_size: int
    total: int
    pages: int

class OrderUpdate(BaseModel):
    kilometraje_orden: int | None = Field(default=None, ge=0)
    proveedor_id: int | None = Field(default=None, gt=0)
    preventivo_ids: list[int] | None = None
    descripcion_correctivo: str | None = Field(default=None, max_length=5000)
    monto: Decimal | None = Field(default=None, ge=0)
    dias_parada: int | None = Field(default=None, ge=0)

class OrderArchiveUpdate(BaseModel):
    estado_archivo: str
    @field_validator("estado_archivo")
    @classmethod
    def validate_state(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in ARCHIVE_STATES: raise ValueError("Estado de archivo inválido")
        return value

class OrderAuditRead(BaseModel):
    accion: str
    fecha_hora: datetime
    usuario: str
    cambios: dict


class OrderVehicleRead(BaseModel):
    id: int
    placa: str
    marca: str | None
    modelo: str | None
    kilometraje_actual: int | None
    estado: str

    model_config = {"from_attributes": True}


class MaintenanceCatalogRead(BaseModel):
    id: int
    id_componente_origen: str
    tarea: str
    prioridad: str | None
    intervalo_km: int | None
    intervalo_dias: int | None

    model_config = {"from_attributes": True}


class ProviderRead(BaseModel):
    id: int
    razon_social: str
    nombre_comercial: str | None

    model_config = {"from_attributes": True}
