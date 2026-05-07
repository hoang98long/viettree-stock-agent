"""RAG-ready interfaces and contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class KnowledgeDocument:
    document_id: str
    symbol: str
    content: str
    metadata: dict


class RetrievalStore(Protocol):
    def upsert_documents(self, documents: list[KnowledgeDocument]) -> None:
        """Persist documents for later retrieval."""

    def similarity_search(
        self,
        *,
        query: str,
        symbol: str | None = None,
        top_k: int = 5,
    ) -> list[KnowledgeDocument]:
        """Retrieve relevant documents."""
