"""Vector retrieval abstraction with Ollama embeddings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import Any

from langchain_ollama import OllamaEmbeddings

from configs.settings import Settings
from rag.interfaces import KnowledgeDocument, RetrievalStore


class BaseVectorStore(RetrievalStore, ABC):
    """Backend-neutral retrieval contract."""

    @abstractmethod
    def upsert_documents(self, documents: list[KnowledgeDocument]) -> None:
        raise NotImplementedError

    @abstractmethod
    def similarity_search(
        self,
        *,
        query: str,
        symbol: str | None = None,
        top_k: int = 5,
    ) -> list[KnowledgeDocument]:
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    """Deterministic fallback store used until Qdrant or Chroma is wired in."""

    def __init__(self, embeddings: OllamaEmbeddings) -> None:
        self.embeddings = embeddings
        self._documents: dict[str, KnowledgeDocument] = {}
        self._vectors: dict[str, list[float]] = {}

    def upsert_documents(self, documents: list[KnowledgeDocument]) -> None:
        if not documents:
            return
        vectors = self.embeddings.embed_documents([document.content for document in documents])
        for document, vector in zip(documents, vectors, strict=True):
            self._documents[document.document_id] = document
            self._vectors[document.document_id] = vector

    def similarity_search(
        self,
        *,
        query: str,
        symbol: str | None = None,
        top_k: int = 5,
    ) -> list[KnowledgeDocument]:
        if not self._documents:
            return []

        query_vector = self.embeddings.embed_query(query)
        candidates = [
            document
            for document in self._documents.values()
            if symbol is None or document.symbol.upper() == symbol.upper()
        ]
        ranked = sorted(
            candidates,
            key=lambda document: _cosine_similarity(
                query_vector,
                self._vectors[document.document_id],
            ),
            reverse=True,
        )
        return ranked[:top_k]


class QdrantVectorStore(BaseVectorStore):
    """Placeholder Qdrant adapter.

    This preserves a clean interface boundary before the concrete client wiring
    is added.
    """

    def __init__(self, settings: Settings, embeddings: OllamaEmbeddings) -> None:
        self.settings = settings
        self.embeddings = embeddings

    def upsert_documents(self, documents: list[KnowledgeDocument]) -> None:
        raise NotImplementedError("Qdrant adapter is not wired yet")

    def similarity_search(
        self,
        *,
        query: str,
        symbol: str | None = None,
        top_k: int = 5,
    ) -> list[KnowledgeDocument]:
        raise NotImplementedError("Qdrant adapter is not wired yet")


class ChromaVectorStore(BaseVectorStore):
    """Placeholder Chroma adapter."""

    def __init__(self, settings: Settings, embeddings: OllamaEmbeddings) -> None:
        self.settings = settings
        self.embeddings = embeddings

    def upsert_documents(self, documents: list[KnowledgeDocument]) -> None:
        raise NotImplementedError("Chroma adapter is not wired yet")

    def similarity_search(
        self,
        *,
        query: str,
        symbol: str | None = None,
        top_k: int = 5,
    ) -> list[KnowledgeDocument]:
        raise NotImplementedError("Chroma adapter is not wired yet")


class RetrievalService:
    """Builds embedding-backed retrieval with backend abstraction."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        )
        self.store = self._build_store()

    def _build_store(self) -> BaseVectorStore:
        backend = self.settings.vector_backend.lower()
        if backend == "qdrant":
            return InMemoryVectorStore(self.embeddings)
        if backend == "chroma":
            return InMemoryVectorStore(self.embeddings)
        return InMemoryVectorStore(self.embeddings)

    def upsert_documents(self, documents: list[KnowledgeDocument]) -> None:
        self.store.upsert_documents(documents)

    def retrieve(
        self,
        *,
        query: str,
        symbol: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        documents = self.store.similarity_search(query=query, symbol=symbol, top_k=top_k)
        return [
            {
                "document_id": document.document_id,
                "symbol": document.symbol,
                "content": document.content,
                "metadata": document.metadata,
            }
            for document in documents
        ]

    # TODO: add semantic search tuning with hybrid metadata + vector filtering.
    # TODO: add ranking pipeline with rerankers, freshness boosts, and source quality weights.


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
