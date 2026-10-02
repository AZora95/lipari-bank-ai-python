"""La categorizzazione a regole: parole chiave, nessun modello. Non costa e non cambia.

È quella che usano i test che non parlano di categorizzazione: la risposta è sempre la stessa.
"""

import re

from src.types.categorize import CategorizeRequest, CategorizeResponse, CategoryEnum

REGOLE: list[tuple[CategoryEnum, str, frozenset[str]]] = [
    ("UTILITIES", "ENERGY", frozenset({"luce", "gas", "enel", "energia", "bolletta"})),
    ("UTILITIES", "WATER", frozenset({"acqua", "acquedotto"})),
    ("UTILITIES", "TELCO", frozenset({"internet", "telefono", "tim", "vodafone", "fastweb"})),
    (
        "GROCERIES",
        "SUPERMARKET",
        frozenset({"supermercato", "esselunga", "conad", "coop", "carrefour", "lidl", "market"}),
    ),
    ("GROCERIES", "FOOD", frozenset({"alimentari", "panificio", "macelleria"})),
    ("TRANSPORT", "FUEL", frozenset({"carburante", "benzina", "gasolio", "distributore"})),
    ("TRANSPORT", "TRAIN", frozenset({"treno", "trenitalia", "italo"})),
    ("TRANSPORT", "PARKING", frozenset({"parcheggio", "telepass", "autostrada"})),
    ("RESTAURANTS", "RESTAURANT", frozenset({"ristorante", "pizzeria", "trattoria", "osteria"})),
    ("RESTAURANTS", "BAR", frozenset({"bar", "caffè", "caffe", "pasticceria"})),
    ("ENTERTAINMENT", "STREAMING", frozenset({"netflix", "spotify", "disney", "dazn"})),
    ("ENTERTAINMENT", "GYM", frozenset({"palestra"})),
    ("ENTERTAINMENT", "CINEMA", frozenset({"cinema", "teatro"})),
]


def categorizza(req: CategorizeRequest) -> CategorizeResponse:
    """La prima regola che trova una sua parola nella descrizione; altrimenti OTHER."""
    parole = set(re.findall(r"\w+", req.description.lower()))
    for categoria, sottocategoria, chiavi in REGOLE:
        if trovate := sorted(parole & chiavi):
            return CategorizeResponse(
                category=categoria,
                subcategory=sottocategoria,
                confidence=0.9,
                reasoning=f"La descrizione contiene «{trovate[0]}».",
            )
    return CategorizeResponse(
        category="OTHER",
        subcategory="UNKNOWN",
        confidence=0.3,
        reasoning="Nessuna regola riconosce la descrizione.",
    )
