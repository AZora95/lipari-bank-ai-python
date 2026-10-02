from openai import AsyncOpenAI


class EmbeddingClient:
    """Gli embedding dall'API compatibile OpenAI: in questo progetto è quella di Ollama, su /v1.

    /v1 restituisce i vettori normalizzati, il vecchio /api/embeddings no: la direzione è la
    stessa, e il retrieval confronta il coseno, quindi l'indice già costruito resta valido.
    """

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client = client
        self.model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # un lotto, una chiamata: l'API accetta la lista intera
        risposta = await self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in sorted(risposta.data, key=lambda d: d.index)]

    async def embed_one(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]
