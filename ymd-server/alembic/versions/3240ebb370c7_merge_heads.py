"""merge heads

Revision ID: 3240ebb370c7
Revises: d3f4a1b2c3d4, 9c0d1e2f3a4b
Create Date: 2026-04-08 12:17:00.428149

"""
from typing import Sequence, Union

from alembic import op


revision: str = "3240ebb370c7"
down_revision: Union[str, None] = ("d3f4a1b2c3d4", "9c0d1e2f3a4b")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
