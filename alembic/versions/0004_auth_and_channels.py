"""add email_password, apple_sub, onboarding fields and connected_channels table

Revision ID: 0004_auth_and_channels
Revises: 0003_celery_task_id
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_auth_and_channels"
down_revision = "0003_celery_task_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("apple_sub", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_users_apple_sub", "users", ["apple_sub"])
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("editing_experience", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("creation_reason", sa.Text(), nullable=True))

    op.create_table(
        "connected_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("platform", sa.String(32), nullable=False, server_default="youtube"),
        sa.Column("channel_id", sa.String(255), nullable=False, index=True),
        sa.Column("channel_title", sa.String(255), nullable=False),
        sa.Column("thumbnail_url", sa.String(1024), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(), nullable=True),
        sa.Column("goals", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("connected_channels")
    op.drop_constraint("uq_users_apple_sub", "users", type_="unique")
    op.drop_column("users", "creation_reason")
    op.drop_column("users", "editing_experience")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "apple_sub")
    op.drop_column("users", "password_hash")
