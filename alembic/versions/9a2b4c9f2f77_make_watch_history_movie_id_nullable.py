"""Make watch_history.movie_id nullable for TV entries.

Revision ID: 9a2b4c9f2f77
Revises: 8b0f3b9b0a2f
Create Date: 2026-02-28 21:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9a2b4c9f2f77"
down_revision = "8b0f3b9b0a2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("watch_history", "movie_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column("watch_history", "movie_id", existing_type=sa.Integer(), nullable=False)
