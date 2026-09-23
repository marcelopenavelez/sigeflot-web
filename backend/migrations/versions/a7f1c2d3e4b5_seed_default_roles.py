"""seed default roles idempotently

Revision ID: a7f1c2d3e4b5
Revises: e25f994a9e6a
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a7f1c2d3e4b5"
down_revision: Union[str, Sequence[str], None] = "e25f994a9e6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLES = (
    ("ADMINISTRADOR", "Administrador", "Administración integral del sistema"),
    ("MECANICO", "Mecánico", "Gestión técnica y mantenimiento vehicular"),
    ("CHOFER", "Chofer", "Consulta de información operativa asignada"),
    ("CONSULTA", "Consulta", "Consulta de información sin modificaciones"),
)


def upgrade() -> None:
    """Insert each required role only when its code does not exist."""
    for codigo, nombre, descripcion in ROLES:
        op.execute(
            "INSERT INTO roles (codigo, nombre, descripcion, activo) "
            f"SELECT '{codigo}', '{nombre}', '{descripcion}', 1 "
            f"WHERE NOT EXISTS (SELECT 1 FROM roles WHERE codigo = '{codigo}')"
        )


def downgrade() -> None:
    """Remove only the standard roles seeded by this revision."""
    op.execute("DELETE FROM roles WHERE codigo IN ('ADMINISTRADOR', 'MECANICO', 'CHOFER', 'CONSULTA')")
