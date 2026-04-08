"""add post media column

Revision ID: 4d2c1a9b8e7f
Revises: 3240ebb370c7
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d2c1a9b8e7f"
down_revision: Union[str, None] = "3240ebb370c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增统一媒体字段（兼容旧 image_urls）
    op.add_column(
        "posts",
        sa.Column("media", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )

    # 迁移历史图片到 media（仅当 image_urls 非空）
    op.execute(
        """
        UPDATE posts
        SET media = (
            SELECT COALESCE(
                json_agg(json_build_object('type', 'image', 'url', x.value)),
                '[]'::json
            )
            FROM json_array_elements_text(posts.image_urls) AS x(value)
        )
        WHERE posts.image_urls IS NOT NULL
          AND json_array_length(posts.image_urls) > 0;
        """
    )


def downgrade() -> None:
    op.drop_column("posts", "media")

