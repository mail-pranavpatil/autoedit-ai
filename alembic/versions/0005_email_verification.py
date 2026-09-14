"""add email verification fields to users table

Revision ID: 0005_email_verification
Revises: 0004_auth_and_channels
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_email_verification"
down_revision = "0004_auth_and_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("verification_code", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("verification_code_expires_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "verification_code_expires_at")
    op.drop_column("users", "verification_code")
    op.drop_column("users", "is_verified")
