"""Preserve repeated BI variants with a workbook row identity."""
from alembic import op
import sqlalchemy as sa
revision = "e5f7a9c1d3e5"
down_revision = "d4e6f8a0b2c4"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("catalogo_mantenimiento_bi_origen", sa.Column("fila_origen", sa.Integer(), nullable=True))
    op.execute("UPDATE catalogo_mantenimiento_bi_origen SET fila_origen = id WHERE fila_origen IS NULL")
    op.alter_column("catalogo_mantenimiento_bi_origen", "fila_origen", existing_type=sa.Integer(), nullable=False)
    op.create_unique_constraint("uq_catalogo_bi_fila_origen", "catalogo_mantenimiento_bi_origen", ["fila_origen"])
def downgrade():
    raise RuntimeError("Source row identities require manual reconciliation before downgrade")
