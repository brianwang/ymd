"""community posts

Revision ID: 5a9f7b6c2e1d
Revises: c9d1b9b4b0e1
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "5a9f7b6c2e1d"
down_revision: Union[str, None] = "c9d1b9b4b0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_urls", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
        sa.Column("like_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_posts_user_id"), "posts", ["user_id"], unique=False)
    op.create_index("ix_posts_created_at", "posts", ["created_at"], unique=False)
    op.create_index("ix_posts_user_created_at", "posts", ["user_id", "created_at"], unique=False)

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comments_post_id"), "comments", ["post_id"], unique=False)
    op.create_index(op.f("ix_comments_user_id"), "comments", ["user_id"], unique=False)
    op.create_index("ix_comments_post_created_at", "comments", ["post_id", "created_at"], unique=False)
    op.create_index("ix_comments_user_created_at", "comments", ["user_id", "created_at"], unique=False)

    op.create_table(
        "post_likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "post_id", name="uq_post_likes_user_post"),
    )
    op.create_index(op.f("ix_post_likes_post_id"), "post_likes", ["post_id"], unique=False)
    op.create_index(op.f("ix_post_likes_user_id"), "post_likes", ["user_id"], unique=False)
    op.create_index("ix_post_likes_post_created_at", "post_likes", ["post_id", "created_at"], unique=False)
    op.create_index("ix_post_likes_user_created_at", "post_likes", ["user_id", "created_at"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_post_likes_user_created_at", table_name="post_likes")
    op.drop_index("ix_post_likes_post_created_at", table_name="post_likes")
    op.drop_index(op.f("ix_post_likes_user_id"), table_name="post_likes")
    op.drop_index(op.f("ix_post_likes_post_id"), table_name="post_likes")
    op.drop_table("post_likes")

    op.drop_index("ix_comments_user_created_at", table_name="comments")
    op.drop_index("ix_comments_post_created_at", table_name="comments")
    op.drop_index(op.f("ix_comments_user_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_post_id"), table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_posts_user_created_at", table_name="posts")
    op.drop_index("ix_posts_created_at", table_name="posts")
    op.drop_index(op.f("ix_posts_user_id"), table_name="posts")
    op.drop_table("posts")
