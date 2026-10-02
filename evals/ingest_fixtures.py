import asyncio
from pathlib import Path
from typing import get_args

from src.db.session import AsyncSessionLocal
from src.llm.factory import get_embedder
from src.services.ingest_service import IngestService
from src.types.advice import IngestRequest

CORPUS = Path("data/docs")
# i livelli sono quelli del Literal del Giorno 6: una lista scritta qui a mano resterebbe indietro
LIVELLI = set(get_args(IngestRequest.model_fields["visibility"].annotation))


async def main() -> None:
    percorsi = await asyncio.to_thread(lambda: sorted(CORPUS.rglob("*.md")))
    if not percorsi:
        # con l'indice vuoto il gate fallirebbe lo stesso, ma per la ragione sbagliata
        raise SystemExit(f"Nessun documento in {CORPUS}/: l'eval non avrebbe niente da recuperare.")
    # il livello è la sottocartella, come in scripts/ingest_docs.py; si controlla tutto
    # PRIMA di ingerire, altrimenti un nome sbagliato lascia l'indice a metà
    livelli = {p: p.parent.name if p.parent != CORPUS else "public" for p in percorsi}
    if sbagliati := [f"{p} «{v}»" for p, v in livelli.items() if v not in LIVELLI]:
        raise SystemExit("Livelli di visibilità inesistenti: " + ", ".join(sbagliati))
    async with AsyncSessionLocal() as session:
        # dalla factory: con Redis, un secondo giro non ricalcola i passaggi già visti
        servizio = IngestService(session, get_embedder())
        for percorso, livello in livelli.items():
            testo = await asyncio.to_thread(percorso.read_text, encoding="utf-8")
            quanti, _ = await servizio.ingest_document(
                percorso.stem, testo, {"source": str(percorso)}, visibility=livello
            )
            print(f"{percorso.stem} [{livello}]: {quanti} passaggi")


if __name__ == "__main__":
    asyncio.run(main())
