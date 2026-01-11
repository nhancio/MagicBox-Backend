"""add oauth_states table for OAuth flows

Revision ID: c2a0b8f1d3e4
Revises: 9c1d2f3a4b5c
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa


revision = "c2a0b8f1d3e4"
down_revision = "9c1d2f3a4b5c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "oauth_states",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("return_to", sa.String(), nullable=True),
        sa.Column("code_verifier", sa.String(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_oauth_states_tenant_id"), "oauth_states", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_oauth_states_user_id"), "oauth_states", ["user_id"], unique=False)
    op.create_index(op.f("ix_oauth_states_project_id"), "oauth_states", ["project_id"], unique=False)
    op.create_index(op.f("ix_oauth_states_provider"), "oauth_states", ["provider"], unique=False)
    op.create_index(op.f("ix_oauth_states_created_at"), "oauth_states", ["created_at"], unique=False)
    op.create_index(op.f("ix_oauth_states_expires_at"), "oauth_states", ["expires_at"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_oauth_states_expires_at"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_created_at"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_provider"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_project_id"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_user_id"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_tenant_id"), table_name="oauth_states")
    op.drop_table("oauth_states")

