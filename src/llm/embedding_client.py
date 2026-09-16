import httpx
from openai import AsyncOpenAI

from src.config import settings


class EmbeddingClient:
    def __init__(self) -> None:
        #self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.base_url = settings.ollama_base_url
        self.model = settings.embedding_model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                response.raise_for_status()
                embeddings.append(response.json()["embedding"])
        return embeddings


    async def embed_one(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]
