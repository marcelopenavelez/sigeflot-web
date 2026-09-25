"""Allow absent source dates in approved historic records."""
from alembic import op
import sqlalchemy as sa
revision = "d4e6f8a0b2c4"
down_revision = "c3d5e7f9a1b2"
branch_labels = None
depends_on = None
def upgrade():
    op.alter_column("ordenes_servicio", "fecha", existing_type=sa.Date(), nullable=True)
    op.alter_column("mantenimientos", "fecha", existing_type=sa.Date(), nullable=True)
def downgrade():
    raise RuntimeError("Historic null dates require manual reconciliation before downgrade")
