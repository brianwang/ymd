"""coliving inquiries

Revision ID: d3f4a1b2c3d4
Revises: 0766a62ad98e
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3f4a1b2c3d4"
down_revision: Union[str, None] = "0766a62ad98e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inquiries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("space_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("contact_name", sa.String(length=50), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'new'"), nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inquiries_created_at"), "inquiries", ["created_at"], unique=False)
    op.create_index(op.f("ix_inquiries_space_id"), "inquiries", ["space_id"], unique=False)
    op.create_index(op.f("ix_inquiries_status"), "inquiries", ["status"], unique=False)
    op.create_index(op.f("ix_inquiries_user_id"), "inquiries", ["user_id"], unique=False)
    op.create_index("ix_inquiries_space_created_at", "inquiries", ["space_id", "created_at"], unique=False)
    op.create_index("ix_inquiries_status_created_at", "inquiries", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_inquiries_status_created_at", table_name="inquiries")
    op.drop_index("ix_inquiries_space_created_at", table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_user_id"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_status"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_space_id"), table_name="inquiries")
    op.drop_index(op.f("ix_inquiries_created_at"), table_name="inquiries")
    op.drop_table("inquiries")
