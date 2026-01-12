"""add agent_id to conversations

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-12 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add agent_id column to conversations table
    op.add_column('conversations', sa.Column('agent_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_conversations_agent_id'), 'conversations', ['agent_id'], unique=False)
    op.create_foreign_key('fk_conversations_agent_id', 'conversations', 'agents', ['agent_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_conversations_agent_id', 'conversations', type_='foreignkey')
    op.drop_index(op.f('ix_conversations_agent_id'), table_name='conversations')
    op.drop_column('conversations', 'agent_id')
