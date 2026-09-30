"""Add service-order document metadata.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
"""

from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "orden_servicio_documentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("orden_servicio_id", sa.Integer(), nullable=False),
        sa.Column("nombre_original", sa.String(255), nullable=False),
        sa.Column("nombre_almacenado", sa.String(80), nullable=False),
        sa.Column("tipo_mime", sa.String(100), nullable=False),
        sa.Column("extension", sa.String(10), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(30), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("fecha_subida", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usuario_subida_id", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint("tamano_bytes > 0", name="ck_orden_documento_tamano_positivo"),
        sa.CheckConstraint(
            "categoria IN ('ORDEN_SERVICIO','FACTURA','INFORME_TECNICO','FOTOGRAFIA','OTRO')",
            name="ck_orden_documento_categoria",
        ),
        sa.ForeignKeyConstraint(["orden_servicio_id"], ["ordenes_servicio.id"], name="fk_documentos_orden_servicio"),
        sa.ForeignKeyConstraint(["usuario_subida_id"], ["usuarios.id"], name="fk_documentos_usuario_subida"),
        sa.UniqueConstraint("storage_key", name="uq_orden_documento_storage_key"),
    )
    op.create_index("ix_orden_documentos_orden_activo", "orden_servicio_documentos", ["orden_servicio_id", "activo"])


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM orden_servicio_documentos")).scalar():
        raise RuntimeError("Cannot downgrade while service-order document metadata exists")
    op.drop_table("orden_servicio_documentos")
