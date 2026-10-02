from functools import lru_cache

from openai import AsyncOpenAI

from src.cache import get_redis
from src.config import settings
from src.llm.anthropic_provider import AnthropicProvider
from src.llm.client import LLMProvider
from src.llm.embedding_client import EmbeddingClient
from src.llm.embeddings import CachedEmbedder
from src.llm.openai_provider import OpenAIProvider
from src.llm.opencode_provider import OpencodeProvider


def provider_per(model: str) -> LLMProvider:
    if model.startswith("gpt"):
        return OpenAIProvider(settings.openai_api_key, model)
    elif model.startswith("claude"):
        return AnthropicProvider(settings.anthropic_api_key, model)
    elif model.startswith("opencode"):
        return OpencodeProvider(settings.opencode_api_key, model)
    else:
        raise ValueError(f"Unknown model: {model}")


def get_llm_provider() -> LLMProvider:
    # senza parametri perché è una dependency: FastAPI farebbe di un parametro una query
    # string, e chiunque potrebbe scegliere il modello, e chi lo paga
    return provider_per(settings.default_model)


@lru_cache
def get_openai() -> AsyncOpenAI:
    # uno per processo, riusato: il pool di connessioni vive nel client (Giorno 4).
    # È l'API compatibile OpenAI di Ollama: la usano l'agente e gli embedding.
    # Ollama ignora la chiave, ma l'SDK ne vuole una; timeout largo: il modello gira in locale
    return AsyncOpenAI(api_key="ollama", base_url=f"{settings.ollama_base_url}/v1", timeout=120.0)


def get_embedder() -> EmbeddingClient:
    # lo stesso modello per i documenti e per le domande: è la regola che non si viola
    base = EmbeddingClient(get_openai(), settings.embedding_model)
    redis = get_redis()  # Giorno 10: con Redis, la cache davanti; senza, il client com'era
    return CachedEmbedder(base, redis) if redis is not None else base
