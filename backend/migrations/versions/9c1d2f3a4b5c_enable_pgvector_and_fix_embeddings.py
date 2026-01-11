"""Enable pgvector extension and migrate embeddings.embedding to VECTOR

Revision ID: 9c1d2f3a4b5c
Revises: e632d777d01d
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c1d2f3a4b5c"
down_revision = "e632d777d01d"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # pgvector is Postgres-only; skip for sqlite dev environments.
        return

    # Ensure extension exists (required for pgvector.sqlalchemy.Vector columns)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # The initial migration created embeddings.embedding as JSON (fallback).
    # The SQLAlchemy model expects VECTOR(1536). Convert safely.
    #
    # Strategy:
    # - Add new vector column
    # - Cast JSON array text representation to vector
    # - Drop old column and rename
    op.execute("ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS embedding_vec vector(1536);")
    op.execute("UPDATE embeddings SET embedding_vec = (embedding::text)::vector WHERE embedding_vec IS NULL;")
    op.execute("ALTER TABLE embeddings ALTER COLUMN embedding_vec SET NOT NULL;")

    # Replace the old JSON column
    op.execute("ALTER TABLE embeddings DROP COLUMN embedding;")
    op.execute("ALTER TABLE embeddings RENAME COLUMN embedding_vec TO embedding;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Re-create JSON column (lossy downgrade)
    op.add_column("embeddings", sa.Column("embedding_json", sa.JSON(), nullable=True))
    op.execute("UPDATE embeddings SET embedding_json = embedding::text::json;")
    op.execute("ALTER TABLE embeddings DROP COLUMN embedding;")
    op.execute("ALTER TABLE embeddings RENAME COLUMN embedding_json TO embedding;")
