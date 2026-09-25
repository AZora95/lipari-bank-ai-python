from pydantic import BaseModel
from sqlalchemy import text as sql
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.acl import visible_to
from src.llm.embedding_client import EmbeddingClient

SOGLIA_PREDEFINITA = 0.35     # misurata sui documenti di LipariBank, non universale


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    similarity: float


class RetrievalService:
    """La ricerca vettoriale sui passaggi dei documenti."""

    SQL = sql(
        """
        SELECT id, document_id, content,
               1 - (embedding <=> CAST(:q AS vector)) AS similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> CAST(:q AS vector)) >= :soglia
        ORDER BY embedding <=> CAST(:q AS vector)
        LIMIT :k
        """
    )

    # la SQL di sopra con UNA riga in piu': AND visibility = ANY(:livelli)
    SQL_PER_RUOLO = sql(
        """
        SELECT id, document_id, content,
               1 - (embedding <=> CAST(:q AS vector)) AS similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> CAST(:q AS vector)) >= :soglia
          AND visibility = ANY(:livelli)
        ORDER BY embedding <=> CAST(:q AS vector)
        LIMIT :k
        """
    )

    def __init__(self, session: AsyncSession, embedder: EmbeddingClient) -> None:
        self.session = session
        self.embedder = embedder

    async def search(
        self, question: str, top_k: int = 5, soglia: float = SOGLIA_PREDEFINITA
    ) -> list[RetrievalResult]:
        """I passaggi più vicini alla domanda, dal più vicino, SENZA filtro per ruolo.

        Solo per ingestione e script, dove non c'è un utente: nessun percorso che parte
        da una richiesta HTTP deve chiamarlo. Sotto la soglia non torna niente.
        """
        query_vec = await self.embedder.embed_one(question)
        righe = await self.session.execute(
            self.SQL, {"q": str(query_vec), "k": top_k, "soglia": soglia}
        )
        return self._risultati(righe)

    async def search_for_user(
        self, query_vec: list[float], role: str, top_k: int = 5
    ) -> list[RetrievalResult]:
        """I passaggi più vicini FRA QUELLI che questo ruolo può vedere."""
        righe = await self.session.execute(
            self.SQL_PER_RUOLO,
            {"q": str(query_vec), "k": top_k, "soglia": SOGLIA_PREDEFINITA,
             "livelli": visible_to(role)},
        )
        return self._risultati(righe)

    @staticmethod
    def _risultati(righe) -> list[RetrievalResult]:
        return [
            RetrievalResult(
                chunk_id=str(r.id),
                document_id=r.document_id,
                content=r.content,
                similarity=float(r.similarity),
            )
            for r in righe
        ]
