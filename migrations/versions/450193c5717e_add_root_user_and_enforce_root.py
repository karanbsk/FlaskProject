"""add root user and enforce root

Revision ID: 450193c5717e
Revises: 394b9460c6c0
Create Date: 2025-09-01 22:33:55.214872

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '450193c5717e'
down_revision = '394b9460c6c0'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns
    op.add_column('users', sa.Column('is_root', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='0'))

    # Seed root user if not exists
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM users WHERE is_root = TRUE"))
    count = result.scalar()

    if count == 0:
        password_hash = generate_password_hash("changeme123")
        conn.execute(
            sa.text(
                """INSERT INTO users (username, email, is_root, force_password_change, password_hash, created_at, updated_at)
                   VALUES (:username, :email, :is_root, :force_password_change, :password_hash, :created_at, :updated_at)"""
            ),
            {
                "username": "root",
                "email": "root@flaskapp.com",
                "is_root": True,
                "force_password_change": True,
                "password_hash": password_hash,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        )


def downgrade():
    op.drop_column('users', 'is_root')
    op.drop_column('users', 'force_password_change')
