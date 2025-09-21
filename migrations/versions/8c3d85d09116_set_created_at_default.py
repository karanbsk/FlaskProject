"""set_created_at_default

Revision ID: 8c3d85d09116
Revises: 450193c5717e
Create Date: 2025-09-14 13:32:56.847779

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c3d85d09116'
down_revision = '450193c5717e'
branch_labels = None
depends_on = None


def upgrade():
    # backfill existing nulls
    op.execute("UPDATE users SET created_at = NOW() WHERE created_at IS NULL")
    # set server default to now() and set NOT NULL
    op.alter_column('users', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.text('NOW()'),
                    nullable=False)


def downgrade():
    op.alter_column('users', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    nullable=True)
