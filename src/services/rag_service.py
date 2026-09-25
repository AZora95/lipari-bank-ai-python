import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path

from src.auth.deps import UserContext
from src.llm.client import LLMProvider, LLMProviderError, LLMResponse, Message
from src.llm.embedding_client import EmbeddingClient
from src.llm.rewriter import QueryRewriter
from src.services.retrieval_service import RetrievalResult, RetrievalService
from src.types.advice import AdviceRequest, AdviceResponse, Citation

logger = logging.getLogger(__name__)

ADVICE_SYSTEM = (
    Path(__file__).parent.parent / "prompts" / "advice_system_v1.md"
).read_text(encoding="utf-8")


@dataclass
class Fasi:
    """Millisecondi per fase, per il log strutturato della richiesta."""

    rewrite_ms: int = 0
    embedding_ms: int = 0
    retrieval_ms: int = 0
    prompt_ms: int = 0
    llm_ms: int = 0
    used_fallback: bool = False

    @property
    def total_ms(self) -> int:
        return (
            self.rewrite_ms + self.embedding_ms + self.retrieval_ms
            + self.prompt_ms + self.llm_ms
        )


@contextmanager
def _cronometro(fasi: Fasi, campo: str) -> Iterator[None]:
    # il finally registra il tempo anche se la fase alza un'eccezione
    inizio = time.perf_counter()
    try:
        yield
    finally:
        setattr(fasi, campo, int((time.perf_counter() - inizio) * 1000))


class RAGService:
    def __init__(
        self,
        rewriter: QueryRewriter,
        embedder: EmbeddingClient,
        retrieval: RetrievalService,
        llm: LLMProvider,
    ) -> None:
        self.rewriter = rewriter
        self.embedder = embedder
        self.retrieval = retrieval
        self.llm = llm

    async def answer(self, req: AdviceRequest, user: UserContext) -> AdviceResponse:
        fasi = Fasi()

        with _cronometro(fasi, "rewrite_ms"):
            search_query = await self.rewriter.rewrite(req.question)

        with _cronometro(fasi, "embedding_ms"):
            query_vec = await self.embedder.embed_one(search_query)

        with _cronometro(fasi, "retrieval_ms"):
            chunks = await self.retrieval.search_for_user(query_vec, user.role, top_k=5)

        if not chunks:
            self._log(fasi, user, chunks)
            return AdviceResponse(
                answer="Non ho documenti correlati alla tua domanda.",
                citations=[],
                tokens_used=0,
                cost_eur=0,
                rewritten_query=search_query,
            )

        with _cronometro(fasi, "prompt_ms"):
            # La riscritta serve al retrieval. Al modello va la domanda dell'utente.
            user_prompt = self._build_prompt(req.question, chunks)

        with _cronometro(fasi, "llm_ms"):
            llm_response, fasi.used_fallback = await self._generate_or_degrade(
                user_prompt, chunks
            )

        self._log(fasi, user, chunks)
        return AdviceResponse(
            answer=llm_response.content,
            citations=[
                Citation(
                    document_id=c.document_id,
                    chunk_id=c.chunk_id,
                    excerpt=c.content[:200] + "..." if len(c.content) > 200 else c.content,
                    similarity=c.similarity,
                )
                for c in chunks
            ],
            tokens_used=llm_response.tokens_used,
            cost_eur=llm_response.cost_eur,
            rewritten_query=search_query,
        )

    @staticmethod
    def _build_prompt(question: str, chunks: list[RetrievalResult]) -> str:
        context = "\n\n---\n\n".join(
            f"[doc_id: {c.document_id}, chunk: {c.chunk_id}, "
            f"similarity: {c.similarity:.2f}]\n{c.content}"
            for c in chunks
        )
        return f"""CONTESTI:
{context}

DOMANDA: {question}

RISPOSTA (con citazioni):"""

    async def _generate_or_degrade(
        self, user_prompt: str, chunks: list[RetrievalResult]
    ) -> tuple[LLMResponse, bool]:
        """Se il generator è giù, restituisce i passaggi migliori invece di un errore."""
        try:
            response = await self.llm.complete(
                messages=[
                    Message(role="system", content=ADVICE_SYSTEM),
                    Message(role="user", content=user_prompt),
                ],
                max_tokens=800,
            )
            return response, False
        except LLMProviderError:
            logger.warning("generator_non_disponibile_fallback_su_chunk")
            estratti = "\n\n".join(
                f"[fonte-{i}] {c.document_id}\n{c.content}"
                for i, c in enumerate(chunks[:3], start=1)
            )
            content = (
                "⚠️ Risposta parziale: il servizio di sintesi non è momentaneamente "
                "disponibile. Di seguito i passaggi dei documenti più pertinenti "
                f"alla tua domanda.\n\n{estratti}"
            )
            return LLMResponse(content=content, tokens_used=0, cost_eur=0, model="fallback"), True

    @staticmethod
    def _log(fasi: Fasi, user: UserContext, chunks: list[RetrievalResult]) -> None:
        # chunk_ids e non il contenuto, e niente testo della domanda accanto allo username
        logger.info(
            "advice_completata",
            extra={
                "username": user.username,
                "role": user.role,
                "chunk_count": len(chunks),
                "chunk_ids": [c.chunk_id for c in chunks],
                "total_ms": fasi.total_ms,
                **asdict(fasi),
            },
        )
