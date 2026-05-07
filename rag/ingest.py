"""RAG ingestion skeleton for stock knowledge documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Iterable

from rag.interfaces import KnowledgeDocument, RetrievalStore


@dataclass(slots=True)
class IngestionRecord:
    document_id: str
    symbol: str
    source_type: str
    title: str
    content: str
    metadata: dict = field(default_factory=dict)


class DocumentIngestionService:
    """Normalizes source records into vector-store-ready knowledge documents."""

    def __init__(self, store: RetrievalStore) -> None:
        self.store = store

    def ingest_records(self, records: Iterable[IngestionRecord]) -> list[KnowledgeDocument]:
        documents = [self._to_document(record) for record in records]
        if documents:
            self.store.upsert_documents(documents)
        return documents

    def _to_document(self, record: IngestionRecord) -> KnowledgeDocument:
        content = self._normalize_content(record.content)
        metadata = {
            "symbol": record.symbol.upper(),
            "source_type": record.source_type,
            "title": record.title,
            **record.metadata,
        }
        document_id = record.document_id or self._build_document_id(record, content)
        return KnowledgeDocument(
            document_id=document_id,
            symbol=record.symbol.upper(),
            content=content,
            metadata=metadata,
        )

    @staticmethod
    def _normalize_content(content: str) -> str:
        normalized = " ".join(content.split())
        if not normalized:
            raise ValueError("ingestion content must not be empty")
        return normalized

    @staticmethod
    def _build_document_id(record: IngestionRecord, content: str) -> str:
        raw = f"{record.symbol}|{record.source_type}|{record.title}|{content}"
        return sha256(raw.encode("utf-8")).hexdigest()

    # TODO: add news ingestion pipeline with source freshness, deduplication, and publisher metadata.
    # TODO: add financial report ingestion with chunking for 10-K, 10-Q, earnings calls, and filings.
