"""events_and_registrations

Revision ID: 1a2b3c4d5e6f
Revises: 0766a62ad98e
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, None] = "0766a62ad98e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("cover_url", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signup_deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("registered_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_category"), "events", ["category"], unique=False)
    op.create_index(op.f("ix_events_city"), "events", ["city"], unique=False)
    op.create_index(op.f("ix_events_is_published"), "events", ["is_published"], unique=False)
    op.create_index(op.f("ix_events_signup_deadline_at"), "events", ["signup_deadline_at"], unique=False)
    op.create_index(op.f("ix_events_start_at"), "events", ["start_at"], unique=False)
    op.create_index(op.f("ix_events_title"), "events", ["title"], unique=False)
    op.create_index("ix_events_published_start_at", "events", ["is_published", "start_at"], unique=False)

    op.create_table(
        "event_registrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="registered", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_registrations_event_user"),
    )
    op.create_index(op.f("ix_event_registrations_event_id"), "event_registrations", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_registrations_status"), "event_registrations", ["status"], unique=False)
    op.create_index(op.f("ix_event_registrations_user_id"), "event_registrations", ["user_id"], unique=False)
    op.create_index("ix_event_registrations_event_status", "event_registrations", ["event_id", "status"], unique=False)
    op.create_index("ix_event_registrations_user_status", "event_registrations", ["user_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_event_registrations_user_status", table_name="event_registrations")
    op.drop_index("ix_event_registrations_event_status", table_name="event_registrations")
    op.drop_index(op.f("ix_event_registrations_user_id"), table_name="event_registrations")
    op.drop_index(op.f("ix_event_registrations_status"), table_name="event_registrations")
    op.drop_index(op.f("ix_event_registrations_event_id"), table_name="event_registrations")
    op.drop_table("event_registrations")

    op.drop_index("ix_events_published_start_at", table_name="events")
    op.drop_index(op.f("ix_events_title"), table_name="events")
    op.drop_index(op.f("ix_events_start_at"), table_name="events")
    op.drop_index(op.f("ix_events_signup_deadline_at"), table_name="events")
    op.drop_index(op.f("ix_events_is_published"), table_name="events")
    op.drop_index(op.f("ix_events_city"), table_name="events")
    op.drop_index(op.f("ix_events_category"), table_name="events")
    op.drop_table("events")

