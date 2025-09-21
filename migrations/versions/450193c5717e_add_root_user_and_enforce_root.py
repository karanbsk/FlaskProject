"""add root user and enforce root

Revision ID: 450193c5717e
Revises: 394b9460c6c0
Create Date: 2025-09-01 22:33:55.214872

"""
from alembic import op, context
import sqlalchemy as sa
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

# revision identifiers, used by Alembic.
revision = '450193c5717e'
down_revision = '394b9460c6c0'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns
    op.add_column('users', sa.Column('is_root', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    if context.is_offline_mode():
        return
    
    # Seed root user if not exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # If 'users' table exists, try to insert root user if none exists
    if 'users' in inspector.get_table_names():
        # Use a safe SELECT returning a row
        res = bind.execute(sa.text("SELECT COUNT(*) as cnt FROM users WHERE is_root = TRUE"))
        row = res.fetchone()
        cnt = row[0] if row is not None else 0
        if cnt == 0:
            init_pw = os.environ.get('INIT_ROOT_PW')
            if init_pw:
                pw_hash = generate_password_hash(init_pw)
            else:
                # fallback - must be rotated in real environments
                pw_hash = generate_password_hash("ChangeMeNow!")
            # Insert a root user (adjust fields/values as required)
            bind.execute(sa.text(
                """
                INSERT INTO users (username, email, is_root, force_password_change, password_hash, created_at, updated_at)
                VALUES (:username, :email, TRUE, FALSE, :pw, now(), now())
                """
            ), {
                "username": "root", 
                "email": "root@flaskapp.com",
                "is_root": True, 
                "force_password_change": True,
                "pw": pw_hash
                } 
            )

def downgrade():
    op.drop_column('users', 'is_root')
    op.drop_column('users', 'force_password_change')
