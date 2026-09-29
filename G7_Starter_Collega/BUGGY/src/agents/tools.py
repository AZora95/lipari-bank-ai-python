import logging
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.agents.registry import Tool
from src.auth.deps import UserContext
from src.db.models import ComplianceAlert
from src.deps import Deps

logger = logging.getLogger(__name__)

DESC_SALDO = (
    "Usalo quando serve il saldo disponibile di un conto per rispondere a una "
    "domanda su capienza, disponibilità o possibilità di disporre un'operazione."
)
DESC_MOVIMENTI = (
    "Usalo quando la domanda riguarda le operazioni recenti di un conto: "
    "importi, date, causali degli ultimi giorni."
)
DESC_DOCS = (
    "Usalo quando la domanda riguarda una procedura, una policy o una soglia "
    "interna di LipariBank, e la risposta va cercata nei documenti ufficiali."
)
DESC_SEGNALAZIONE = (
    "Usalo quando un'operazione va segnalata alla funzione compliance perché "
    "supera una soglia o ricade in una policy che richiede verifica."
)


def build_tools_for(user: UserContext, deps: Deps) -> list[Tool]:
    """Costruisce i tool per questa richiesta."""

    class SaldoArgs(BaseModel):
        account_id: str = Field(description="L'IBAN del conto da consultare.")

    async def get_account_balance(args: SaldoArgs) -> str:
        saldo = await deps.accounts.balance(args.account_id)
        return f"saldo_disponibile={saldo} valuta=EUR conto={args.account_id}"

    class MovimentiArgs(BaseModel):
        account_id: str = Field(description="L'IBAN del conto da consultare.")
        giorni: int = Field(default=30, ge=1, le=365)

    async def list_recent_movements(args: MovimentiArgs) -> str:
        righe = await deps.accounts.movements(args.account_id, giorni=args.giorni)
        if not righe:
            return "nessun movimento nel periodo richiesto"
        return "\n".join(
            f"{m.data:%Y-%m-%d} {m.importo:>10} {m.causale}" for m in righe
        )

    class DocsArgs(BaseModel):
        query: str = Field(description="La domanda, in forma completa.")

    async def search_documents(args: DocsArgs) -> str:
        vec = await deps.embedder.embed(args.query)
        chunks = await deps.retrieval.search_for_user(vec, role=user.role, top_k=3)
        if not chunks:
            return "nessun documento pertinente"
        return "\n".join(f"[{c.document_id}] {c.content[:400]}" for c, _ in chunks)

    class SegnalazioneArgs(BaseModel):
        account_id: str = Field(description="L'IBAN del conto coinvolto.")
        reason: str = Field(description="Perché l'operazione va segnalata.")

    async def apri_segnalazione_compliance(args: SegnalazioneArgs) -> str:
        alert = ComplianceAlert(
            account_id=args.account_id,
            opened_by=user.username,
            reason=args.reason,
            created_at=datetime.now(UTC),
        )
        deps.session.add(alert)
        await deps.session.commit()
        logger.info("segnalazione aperta id=%s conto=%s", alert.id, args.account_id)
        return f"segnalazione aperta con id {alert.id}"

    return [
        Tool("get_account_balance", DESC_SALDO, SaldoArgs, get_account_balance),
        Tool("list_recent_movements", DESC_MOVIMENTI, MovimentiArgs, list_recent_movements),
        Tool("search_documents", DESC_DOCS, DocsArgs, search_documents),
        Tool(
            "apri_segnalazione_compliance",
            DESC_SEGNALAZIONE,
            SegnalazioneArgs,
            apri_segnalazione_compliance,
        ),
    ]
