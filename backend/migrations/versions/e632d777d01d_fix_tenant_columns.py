"""fix_tenant_columns

Revision ID: e632d777d01d
Revises: 670e29479383
Create Date: 2026-01-11 15:19:14.930448
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e632d777d01d'
down_revision = '670e29479383'
branch_labels = None
depends_on = None

def upgrade():
    # Add missing columns to tenants table
    op.add_column('tenants', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('tenants', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    op.add_column('tenants', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    
    # Update existing rows with default values
    op.execute("UPDATE tenants SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE tenants SET created_at = NOW() WHERE created_at IS NULL")
    op.execute("UPDATE tenants SET updated_at = NOW() WHERE updated_at IS NULL")
    
    # Make columns non-nullable after setting defaults
    op.alter_column('tenants', 'is_active', nullable=False)
    op.alter_column('tenants', 'created_at', nullable=False)
    op.alter_column('tenants', 'updated_at', nullable=False)

def downgrade():
    op.drop_column('tenants', 'updated_at')
    op.drop_column('tenants', 'created_at')
    op.drop_column('tenants', 'is_active')
