"""points ledger and inviter

Revision ID: c9d1b9b4b0e1
Revises: b47873357438
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9d1b9b4b0e1"
down_revision: Union[str, None] = "b47873357438"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("inviter_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_users_inviter_id"), "users", ["inviter_id"], unique=False)
    op.create_foreign_key(
        "fk_users_inviter_id_users",
        "users",
        "users",
        ["inviter_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "points_ledger",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("biz_key", sa.String(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "biz_key", name="uq_points_ledger_user_biz_key"),
    )
    op.create_index(op.f("ix_points_ledger_event_type"), "points_ledger", ["event_type"], unique=False)
    op.create_index(op.f("ix_points_ledger_user_id"), "points_ledger", ["user_id"], unique=False)
    op.create_index("ix_points_ledger_user_created_at", "points_ledger", ["user_id", "created_at"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_points_ledger_user_created_at", table_name="points_ledger")
    op.drop_index(op.f("ix_points_ledger_user_id"), table_name="points_ledger")
    op.drop_index(op.f("ix_points_ledger_event_type"), table_name="points_ledger")
    op.drop_table("points_ledger")

    op.drop_constraint("fk_users_inviter_id_users", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_inviter_id"), table_name="users")
    op.drop_column("users", "inviter_id")
