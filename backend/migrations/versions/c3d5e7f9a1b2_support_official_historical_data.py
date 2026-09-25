"""support official historical data

Revision ID: c3d5e7f9a1b2
Revises: b8e2f4a6c9d1
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d5e7f9a1b2"
down_revision = "b8e2f4a6c9d1"
branch_labels = None
depends_on = None

def _origin(table):
    op.add_column(table, sa.Column("es_historico", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column(table, sa.Column("fuente_origen", sa.String(100), nullable=True))

def upgrade():
    for table in ("vehiculos", "conductores", "proveedores", "salidas", "ordenes_servicio", "mantenimientos"):
        _origin(table)
    op.add_column("vehiculos", sa.Column("marca_modelo_origen", sa.String(200), nullable=True))
    op.add_column("vehiculos", sa.Column("fecha_inactividad", sa.Date(), nullable=True))
    op.add_column("vehiculos", sa.Column("causal_inactividad", sa.Text(), nullable=True))
    op.alter_column("vehiculos", "marca", existing_type=sa.String(80), nullable=True)
    op.alter_column("vehiculos", "modelo", existing_type=sa.String(80), nullable=True)
    op.alter_column("vehiculos", "tipo", existing_type=sa.String(50), nullable=True)
    op.alter_column("vehiculos", "kilometraje_actual", existing_type=sa.Integer(), nullable=True)
    op.alter_column("conductores", "nombres", existing_type=sa.String(100), nullable=True)
    op.alter_column("conductores", "apellidos", existing_type=sa.String(100), nullable=True)
    op.alter_column("conductores", "documento", existing_type=sa.String(30), nullable=True)
    op.alter_column("proveedores", "ruc", existing_type=sa.String(20), nullable=True)
    op.alter_column("salidas", "conductor_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("salidas", "destino", existing_type=sa.String(255), nullable=True)
    op.alter_column("salidas", "motivo", existing_type=sa.Text(), nullable=True)
    op.alter_column("ordenes_servicio", "vehiculo_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("ordenes_servicio", "proveedor_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("mantenimientos", "vehiculo_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("mantenimientos", "tipo", existing_type=sa.String(20), nullable=True)
    op.create_table("catalogo_mantenimiento_origen", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("id_componente_origen", sa.String(100), nullable=False, unique=True), sa.Column("tarea", sa.Text(), nullable=False), sa.Column("prioridad", sa.String(50)), sa.Column("intervalo_km", sa.Integer()), sa.Column("intervalo_dias", sa.Integer()), sa.Column("umbral_alerta", sa.Numeric(8,4)), sa.Column("umbral_critico", sa.Numeric(8,4)))
    op.create_table("catalogo_mantenimiento_bi_origen", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("variante", sa.Text(), nullable=False), sa.Column("tarea_estandarizada", sa.Text()), sa.Column("tipo", sa.String(50)))

def downgrade():
    raise RuntimeError("Historical records require manual reconciliation before downgrade")
