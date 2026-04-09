"""enable location recommendations (user/event/post)

Revision ID: 1f3c2d4e5a6b
Revises: de8a0eb1fda1
Create Date: 2026-04-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1f3c2d4e5a6b"
down_revision: Union[str, None] = "de8a0eb1fda1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_location_lat", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("preferred_location_lng", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("preferred_location_display_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("preferred_location_city", sa.String(), nullable=True))
    op.add_column("users", sa.Column("preferred_location_source", sa.String(), nullable=True))
    op.add_column("users", sa.Column("preferred_location_updated_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("events", sa.Column("lat", sa.Float(), nullable=True))
    op.add_column("events", sa.Column("lng", sa.Float(), nullable=True))

    op.add_column("posts", sa.Column("lat", sa.Float(), nullable=True))
    op.add_column("posts", sa.Column("lng", sa.Float(), nullable=True))
    op.add_column("posts", sa.Column("city", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "city")
    op.drop_column("posts", "lng")
    op.drop_column("posts", "lat")

    op.drop_column("events", "lng")
    op.drop_column("events", "lat")

    op.drop_column("users", "preferred_location_updated_at")
    op.drop_column("users", "preferred_location_source")
    op.drop_column("users", "preferred_location_city")
    op.drop_column("users", "preferred_location_display_name")
    op.drop_column("users", "preferred_location_lng")
    op.drop_column("users", "preferred_location_lat")
