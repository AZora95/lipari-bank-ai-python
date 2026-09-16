"""add pgvector

Revision ID: f441f0dcfc89
Revises: 5dba50630ac2
Create Date: 2026-09-15 09:36:43.118280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'f441f0dcfc89'
down_revision: Union[str, Sequence[str], None] = '5dba50630ac2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("document_id", sa.String, nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(768)),
        sa.Column("chunk_metadata", sa.JSON, default={}),
    )
    op.execute("CREATE INDEX ix_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops)")

def downgrade() -> None:
    """Downgrade schema."""
    pass
