"""Add operational service-order fields and preventive detail.

Revision ID: f9a1b2c3d4e5
Revises: e5f7a9c1d3e5
"""

from alembic import op
import sqlalchemy as sa


revision = "f9a1b2c3d4e5"
down_revision = "e5f7a9c1d3e5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ordenes_servicio", sa.Column("kilometraje_orden", sa.Integer(), nullable=True))
    op.add_column("ordenes_servicio", sa.Column("dias_parada", sa.Integer(), nullable=True))
    op.add_column("ordenes_servicio", sa.Column("estado_archivo", sa.String(length=20), nullable=True))
    op.add_column("ordenes_servicio", sa.Column("descripcion_correctivo", sa.Text(), nullable=True))
    op.execute("UPDATE ordenes_servicio SET estado_archivo = estado WHERE es_historico = 1")
    op.drop_constraint("ck_ordenes_monto", "ordenes_servicio", type_="check")
    op.alter_column("ordenes_servicio", "monto", existing_type=sa.Numeric(12, 2), nullable=True)
    op.create_check_constraint("ck_ordenes_monto", "ordenes_servicio", "monto IS NULL OR monto >= 0")
    op.create_check_constraint("ck_ordenes_kilometraje_orden", "ordenes_servicio", "kilometraje_orden IS NULL OR kilometraje_orden >= 0")
    op.create_check_constraint("ck_ordenes_dias_parada", "ordenes_servicio", "dias_parada IS NULL OR dias_parada >= 0")
    op.create_table(
        "orden_servicio_preventivos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("orden_servicio_id", sa.Integer(), nullable=False),
        sa.Column("catalogo_mantenimiento_origen_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["orden_servicio_id"], ["ordenes_servicio.id"]),
        sa.ForeignKeyConstraint(["catalogo_mantenimiento_origen_id"], ["catalogo_mantenimiento_origen.id"]),
        sa.UniqueConstraint("orden_servicio_id", "catalogo_mantenimiento_origen_id", name="uq_orden_servicio_preventivo_catalogo"),
    )


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM ordenes_servicio WHERE monto IS NULL")).scalar():
        raise RuntimeError("Cannot downgrade while operational service orders have a NULL monto")
    if bind.execute(sa.text("SELECT COUNT(*) FROM orden_servicio_preventivos")).scalar():
        raise RuntimeError("Cannot downgrade while preventive order details exist")
    if bind.execute(sa.text("SELECT COUNT(*) FROM ordenes_servicio WHERE es_historico = 0 AND (kilometraje_orden IS NOT NULL OR dias_parada IS NOT NULL OR estado_archivo IS NOT NULL OR descripcion_correctivo IS NOT NULL)")).scalar():
        raise RuntimeError("Cannot downgrade while operational service-order fields contain data")
    op.drop_table("orden_servicio_preventivos")
    op.drop_constraint("ck_ordenes_dias_parada", "ordenes_servicio", type_="check")
    op.drop_constraint("ck_ordenes_kilometraje_orden", "ordenes_servicio", type_="check")
    op.drop_constraint("ck_ordenes_monto", "ordenes_servicio", type_="check")
    op.alter_column("ordenes_servicio", "monto", existing_type=sa.Numeric(12, 2), nullable=False)
    op.create_check_constraint("ck_ordenes_monto", "ordenes_servicio", "monto >= 0")
    op.drop_column("ordenes_servicio", "descripcion_correctivo")
    op.drop_column("ordenes_servicio", "estado_archivo")
    op.drop_column("ordenes_servicio", "dias_parada")
    op.drop_column("ordenes_servicio", "kilometraje_orden")
