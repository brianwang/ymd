"""add post location and tags

Revision ID: e4c1d2f3a4b5
Revises: de8a0eb1fda1
Create Date: 2026-04-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e4c1d2f3a4b5"
down_revision: Union[str, None] = "de8a0eb1fda1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # location：可选 JSONB 对象
    op.add_column("posts", sa.Column("location", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # tags：JSONB 数组，默认 []
    op.add_column(
        "posts",
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("posts", "tags")
    op.drop_column("posts", "location")

