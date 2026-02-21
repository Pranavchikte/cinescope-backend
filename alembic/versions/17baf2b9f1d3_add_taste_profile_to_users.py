"""add taste profile fields to users

Revision ID: 17baf2b9f1d3
Revises: 8b0f3b9b0a2f
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "17baf2b9f1d3"
down_revision = "8b0f3b9b0a2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_movie_genres", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("preferred_tv_genres", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("preferred_languages", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("taste_onboarded", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.alter_column("users", "taste_onboarded", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "taste_onboarded")
    op.drop_column("users", "preferred_languages")
    op.drop_column("users", "preferred_tv_genres")
    op.drop_column("users", "preferred_movie_genres")
