"""add channel_stats_snapshots table for tracking real YouTube growth over time

Revision ID: 0006_channel_stats_history
Revises: 0005_email_verification
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_channel_stats_history"
down_revision = "0005_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channel_stats_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connected_channels.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("views", sa.BigInteger(), nullable=False),
        sa.Column("subscribers", sa.Integer(), nullable=False),
        sa.Column("video_count", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_channel_stats_snapshots_channel_captured",
        "channel_stats_snapshots",
        ["channel_id", "captured_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_channel_stats_snapshots_channel_captured", table_name="channel_stats_snapshots")
    op.drop_table("channel_stats_snapshots")
