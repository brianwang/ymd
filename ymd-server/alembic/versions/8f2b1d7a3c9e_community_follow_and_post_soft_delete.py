"""community follow and post soft delete

Revision ID: 8f2b1d7a3c9e
Revises: 5a9f7b6c2e1d
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f2b1d7a3c9e"
down_revision: Union[str, None] = "5a9f7b6c2e1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "user_follows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("follower_user_id", sa.Integer(), nullable=False),
        sa.Column("following_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["follower_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["following_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("follower_user_id", "following_user_id", name="uq_user_follows_pair"),
    )
    op.create_index(op.f("ix_user_follows_follower_user_id"), "user_follows", ["follower_user_id"], unique=False)
    op.create_index(op.f("ix_user_follows_following_user_id"), "user_follows", ["following_user_id"], unique=False)
    op.create_index(
        "ix_user_follows_follower_created_at",
        "user_follows",
        ["follower_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_follows_following_created_at",
        "user_follows",
        ["following_user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_follows_following_created_at", table_name="user_follows")
    op.drop_index("ix_user_follows_follower_created_at", table_name="user_follows")
    op.drop_index(op.f("ix_user_follows_following_user_id"), table_name="user_follows")
    op.drop_index(op.f("ix_user_follows_follower_user_id"), table_name="user_follows")
    op.drop_table("user_follows")

    op.drop_column("posts", "deleted_at")

