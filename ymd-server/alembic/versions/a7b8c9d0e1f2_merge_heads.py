"""merge heads (phone + location recommendations + post location/tags)

Revision ID: a7b8c9d0e1f2
Revises: 1f3c2d4e5a6b, e4c1d2f3a4b5, f2a708963a2a
Create Date: 2026-04-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = ("1f3c2d4e5a6b", "e4c1d2f3a4b5", "f2a708963a2a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
