from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DocumentChunk
from src.lib.chunking import chunk_text
from src.llm.embedding_client import EmbeddingClient


class IngestService:
    def __init__(self, session: AsyncSession, embedding_client: EmbeddingClient) -> None:
        self.session = session
        self.embedding_client = embedding_client

    async def ingest_document(
        self,
        document_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        visibility: str = "public",  # il livello che l'ACL del Giorno 6 confronta col ruolo
    ) -> tuple[int, int]:
        """Ingest a document. Returns (chunk_count, embedding_dim)."""
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        embeddings = await self.embedding_client.embed(chunks)

        # reingerire un documento lo sostituisce: due copie degli stessi passaggi occuperebbero
        # due posti nel top-k. La DELETE si conferma insieme agli inserimenti, nel commit sotto
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                content=chunk,
                embedding=embedding,
                chunk_metadata=metadata or {},
                visibility=visibility,
            )
            self.session.add(db_chunk)

        await self.session.commit()
        embedding_dim = len(embeddings[0]) if embeddings else 0
        return len(chunks), embedding_dim

    ingest = ingest_document  # il nome del Code Blueprint, che i test usano: stessi argomenti
