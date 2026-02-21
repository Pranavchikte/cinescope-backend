"""add last_viewed fields to users

Revision ID: 8b0f3b9b0a2f
Revises: 4be78736bd87
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8b0f3b9b0a2f"
down_revision = "4be78736bd87"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_viewed_tmdb_id", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "last_viewed_media_type",
            sa.Enum("movie", "tv", name="mediatype"),
            nullable=True,
        ),
    )
    op.add_column("users", sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_viewed_at")
    op.drop_column("users", "last_viewed_media_type")
    op.drop_column("users", "last_viewed_tmdb_id")
