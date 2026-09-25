"""add official source identifiers for controlled migration

Revision ID: b8e2f4a6c9d1
Revises: a7f1c2d3e4b5
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b8e2f4a6c9d1"
down_revision: Union[str, Sequence[str], None] = "a7f1c2d3e4b5"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("conductores", sa.Column("id_chofer_origen", sa.String(100), nullable=True))
    op.create_unique_constraint("uq_conductores_id_chofer_origen", "conductores", ["id_chofer_origen"])
    op.add_column("salidas", sa.Column("id_salida_origen", sa.String(100), nullable=True))
    op.create_unique_constraint("uq_salidas_id_salida_origen", "salidas", ["id_salida_origen"])
    op.add_column("ordenes_servicio", sa.Column("id_orden_origen", sa.String(100), nullable=True))
    op.create_unique_constraint("uq_ordenes_id_orden_origen", "ordenes_servicio", ["id_orden_origen"])
    op.add_column("mantenimientos", sa.Column("id_registro_origen", sa.String(100), nullable=True))
    op.add_column("mantenimientos", sa.Column("orden_servicio_origen", sa.String(100), nullable=True))
    op.create_unique_constraint("uq_mantenimientos_id_registro_origen", "mantenimientos", ["id_registro_origen"])

def downgrade() -> None:
    op.drop_constraint("uq_mantenimientos_id_registro_origen", "mantenimientos", type_="unique")
    op.drop_column("mantenimientos", "orden_servicio_origen")
    op.drop_column("mantenimientos", "id_registro_origen")
    op.drop_constraint("uq_ordenes_id_orden_origen", "ordenes_servicio", type_="unique")
    op.drop_column("ordenes_servicio", "id_orden_origen")
    op.drop_constraint("uq_salidas_id_salida_origen", "salidas", type_="unique")
    op.drop_column("salidas", "id_salida_origen")
    op.drop_constraint("uq_conductores_id_chofer_origen", "conductores", type_="unique")
    op.drop_column("conductores", "id_chofer_origen")
