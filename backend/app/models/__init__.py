from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rol: Mapped[Role] = relationship(back_populates="usuarios")


class Vehiculo(TimestampMixin, Base):
    __tablename__ = "vehiculos"
    __table_args__ = (CheckConstraint("kilometraje_actual >= 0", name="ck_vehiculos_kilometraje"), CheckConstraint("estado IN ('OPERATIVO','MANTENIMIENTO','INACTIVO')", name="ck_vehiculos_estado"))
    id: Mapped[int] = mapped_column(primary_key=True)
    placa: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    marca: Mapped[str | None] = mapped_column(String(80))
    modelo: Mapped[str | None] = mapped_column(String(80))
    marca_modelo_origen: Mapped[str | None] = mapped_column(String(200))
    anio: Mapped[int | None] = mapped_column(Integer)
    tipo: Mapped[str | None] = mapped_column(String(50))
    kilometraje_actual: Mapped[int | None] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20), default="OPERATIVO", nullable=False)
    soat_vencimiento: Mapped[date | None] = mapped_column(Date)
    revision_tecnica_vencimiento: Mapped[date | None] = mapped_column(Date)
    observaciones: Mapped[str | None] = mapped_column(Text)
    es_historico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fuente_origen: Mapped[str | None] = mapped_column(String(100))
    fecha_inactividad: Mapped[date | None] = mapped_column(Date)
    causal_inactividad: Mapped[str | None] = mapped_column(Text)
    salidas: Mapped[list["Salida"]] = relationship(back_populates="vehiculo")


class Conductor(TimestampMixin, Base):
    __tablename__ = "conductores"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_chofer_origen: Mapped[str | None] = mapped_column(String(100), unique=True)
    nombres: Mapped[str | None] = mapped_column(String(100))
    apellidos: Mapped[str | None] = mapped_column(String(100))
    documento: Mapped[str | None] = mapped_column(String(30), unique=True)
    numero_licencia: Mapped[str | None] = mapped_column(String(30), unique=True)
    categoria_licencia: Mapped[str | None] = mapped_column(String(20))
    licencia_vencimiento: Mapped[date | None] = mapped_column(Date)
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    es_historico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fuente_origen: Mapped[str | None] = mapped_column(String(100))
    salidas: Mapped[list["Salida"]] = relationship(back_populates="conductor")


class Proveedor(TimestampMixin, Base):
    __tablename__ = "proveedores"
    id: Mapped[int] = mapped_column(primary_key=True)
    ruc: Mapped[str | None] = mapped_column(String(20), unique=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_comercial: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    direccion: Mapped[str | None] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    es_historico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fuente_origen: Mapped[str | None] = mapped_column(String(100))


class Salida(TimestampMixin, Base):
    __tablename__ = "salidas"
    __table_args__ = (CheckConstraint("kilometraje_salida >= 0", name="ck_salidas_km_salida"), CheckConstraint("kilometraje_retorno IS NULL OR kilometraje_retorno >= 0", name="ck_salidas_km_retorno"))
    id: Mapped[int] = mapped_column(primary_key=True)
    id_salida_origen: Mapped[str | None] = mapped_column(String(100), unique=True)
    vehiculo_id: Mapped[int] = mapped_column(ForeignKey("vehiculos.id"), nullable=False)
    conductor_id: Mapped[int | None] = mapped_column(ForeignKey("conductores.id"))
    fecha_hora_salida: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kilometraje_salida: Mapped[int] = mapped_column(Integer, nullable=False)
    destino: Mapped[str | None] = mapped_column(String(255))
    motivo: Mapped[str | None] = mapped_column(Text)
    fecha_hora_retorno: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kilometraje_retorno: Mapped[int | None] = mapped_column(Integer)
    observaciones: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="ABIERTA", nullable=False)
    es_historico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fuente_origen: Mapped[str | None] = mapped_column(String(100))
    vehiculo: Mapped[Vehiculo] = relationship(back_populates="salidas")
    conductor: Mapped[Conductor] = relationship(back_populates="salidas")


class OrdenServicio(TimestampMixin, Base):
    __tablename__ = "ordenes_servicio"
    __table_args__ = (CheckConstraint("monto >= 0", name="ck_ordenes_monto"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    id_orden_origen: Mapped[str | None] = mapped_column(String(100), unique=True)
    numero_orden: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    vehiculo_id: Mapped[int | None] = mapped_column(ForeignKey("vehiculos.id"))
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id"))
    fecha: Mapped[date | None] = mapped_column(Date)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="ABIERTA", nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text)
    es_historico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fuente_origen: Mapped[str | None] = mapped_column(String(100))


class Mantenimiento(TimestampMixin, Base):
    __tablename__ = "mantenimientos"
    __table_args__ = (CheckConstraint("kilometraje >= 0", name="ck_mantenimientos_km"), CheckConstraint("costo >= 0", name="ck_mantenimientos_costo"), CheckConstraint("tipo IN ('PREVENTIVO','CORRECTIVO')", name="ck_mantenimientos_tipo"))
    id: Mapped[int] = mapped_column(primary_key=True)
    id_registro_origen: Mapped[str | None] = mapped_column(String(100), unique=True)
    orden_servicio_origen: Mapped[str | None] = mapped_column(String(100))
    vehiculo_id: Mapped[int | None] = mapped_column(ForeignKey("vehiculos.id"))
    orden_servicio_id: Mapped[int | None] = mapped_column(ForeignKey("ordenes_servicio.id"))
    tipo: Mapped[str | None] = mapped_column(String(20))
    fecha: Mapped[date | None] = mapped_column(Date)
    kilometraje: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    costo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)
    proximo_mantenimiento_fecha: Mapped[date | None] = mapped_column(Date)
    proximo_mantenimiento_km: Mapped[int | None] = mapped_column(Integer)
    es_historico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fuente_origen: Mapped[str | None] = mapped_column(String(100))


class CatalogoMantenimientoOrigen(Base):
    __tablename__ = "catalogo_mantenimiento_origen"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_componente_origen: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tarea: Mapped[str] = mapped_column(Text, nullable=False)
    prioridad: Mapped[str | None] = mapped_column(String(50))
    intervalo_km: Mapped[int | None] = mapped_column(Integer)
    intervalo_dias: Mapped[int | None] = mapped_column(Integer)
    umbral_alerta: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    umbral_critico: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))


class CatalogoMantenimientoBIOrigen(Base):
    __tablename__ = "catalogo_mantenimiento_bi_origen"
    id: Mapped[int] = mapped_column(primary_key=True)
    fila_origen: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    variante: Mapped[str] = mapped_column(Text, nullable=False)
    tarea_estandarizada: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str | None] = mapped_column(String(50))
