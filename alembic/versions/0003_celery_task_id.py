"""track the celery task id per video, for cancellation

Revision ID: 0003_celery_task_id
Revises: 0002_youtube
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_celery_task_id"
down_revision = "0002_youtube"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("videos", sa.Column("celery_task_id", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("videos", "celery_task_id")
