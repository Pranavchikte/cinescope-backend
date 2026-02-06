"""add email verification fields to users

Revision ID: add_email_verification
Revises: 
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_email_verification'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column with default False, nullable first
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), nullable=True))
    
    # Set all existing users to verified (since they're already using the app)
    op.execute("UPDATE users SET is_email_verified = true WHERE is_email_verified IS NULL")
    
    # Now make it NOT NULL
    op.alter_column('users', 'is_email_verified', nullable=False)
    
    # Add email_verified_at column
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    
    # Set verified_at for existing users
    op.execute("UPDATE users SET email_verified_at = created_at WHERE is_email_verified = true")


def downgrade() -> None:
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'is_email_verified')