"""Allow absent official maintenance mileage without inventing zero.

Revision ID: a9b8c7d6e5f4
Revises: f9a1b2c3d4e5
"""

from alembic import op
import sqlalchemy as sa


revision = "a9b8c7d6e5f4"
down_revision = "f9a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("mantenimientos", "kilometraje", existing_type=sa.Integer(), nullable=True)


def downgrade():
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM mantenimientos WHERE kilometraje IS NULL")).scalar():
        raise RuntimeError("Cannot downgrade while maintenance records have a NULL kilometraje")
    op.alter_column("mantenimientos", "kilometraje", existing_type=sa.Integer(), nullable=False)
