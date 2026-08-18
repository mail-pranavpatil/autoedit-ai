"""youtube uploads and auto-upload flag

Revision ID: 0002_youtube
Revises: 0001_initial
Create Date: 2026-08-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_youtube"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("youtube_auto_upload", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "youtube_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("youtube_video_id", sa.String(64), nullable=True),
        sa.Column("youtube_url", sa.String(512), nullable=True),
        sa.Column("title", sa.String(128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("video_id", name="uq_youtube_video_id"),
        sa.UniqueConstraint("user_id", "scheduled_at", name="uq_youtube_user_slot"),
    )
    op.create_index("ix_youtube_uploads_user_id", "youtube_uploads", ["user_id"])
    op.create_index("ix_youtube_uploads_status", "youtube_uploads", ["status"])


def downgrade() -> None:
    op.drop_index("ix_youtube_uploads_status", table_name="youtube_uploads")
    op.drop_index("ix_youtube_uploads_user_id", table_name="youtube_uploads")
    op.drop_table("youtube_uploads")
    op.drop_column("users", "youtube_auto_upload")
