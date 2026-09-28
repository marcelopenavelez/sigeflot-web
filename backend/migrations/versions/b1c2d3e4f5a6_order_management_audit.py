"""Add service-order closure and audit fields."""
from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5a6"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("ordenes_servicio", sa.Column("fecha_hora_cierre", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ordenes_servicio", sa.Column("cerrado_por_usuario_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_ordenes_cerrado_por_usuario", "ordenes_servicio", "usuarios", ["cerrado_por_usuario_id"], ["id"])
    op.create_table("orden_servicio_auditoria", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("orden_servicio_id", sa.Integer(), nullable=False), sa.Column("usuario_id", sa.Integer(), nullable=False), sa.Column("accion", sa.String(40), nullable=False), sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False), sa.Column("cambios", sa.JSON(), nullable=False), sa.ForeignKeyConstraint(["orden_servicio_id"], ["ordenes_servicio.id"]), sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]))

def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM orden_servicio_auditoria")).scalar():
        raise RuntimeError("Cannot downgrade while order audit entries exist")
    if bind.execute(sa.text("SELECT COUNT(*) FROM ordenes_servicio WHERE fecha_hora_cierre IS NOT NULL OR cerrado_por_usuario_id IS NOT NULL")).scalar():
        raise RuntimeError("Cannot downgrade while closure data exists")
    op.drop_table("orden_servicio_auditoria")
    op.drop_constraint("fk_ordenes_cerrado_por_usuario", "ordenes_servicio", type_="foreignkey")
    op.drop_column("ordenes_servicio", "cerrado_por_usuario_id")
    op.drop_column("ordenes_servicio", "fecha_hora_cierre")
