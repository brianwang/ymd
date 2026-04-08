"""merge heads

Revision ID: 9c0d1e2f3a4b
Revises: 1a2b3c4d5e6f, 8f2b1d7a3c9e
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "9c0d1e2f3a4b"
down_revision: Union[str, None] = ("1a2b3c4d5e6f", "8f2b1d7a3c9e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

