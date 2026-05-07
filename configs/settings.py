"""Central application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = Field(default="development")
    app_name: str = Field(default="stock-agent-ai")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_reload: bool = Field(default=False)

    postgres_db: str = Field(default="stock_agent")
    postgres_user: str = Field(default="stock")
    postgres_password: str = Field(default="stock")
    postgres_port: int = Field(default=5432)
    postgres_url: str = Field(
        default="postgresql+psycopg2://stock:stock@postgres:5432/stock_agent"
    )

    redis_port: int = Field(default=6379)
    redis_url: str = Field(default="redis://redis:6379/0")
    redis_analysis_queue: str = Field(default="stock-analysis-requests")

    ollama_base_url: str = Field(default="http://ollama:11434")
    ollama_port: int = Field(default=11434)
    ollama_reasoning_model: str = Field(default="llama3.1:8b")
    ollama_embedding_model: str = Field(default="nomic-embed-text")

    qdrant_url: str = Field(default="http://qdrant:6333")
    qdrant_port: int = Field(default=6333)
    qdrant_grpc_port: int = Field(default=6334)
    vector_backend: str = Field(default="qdrant")
    vector_collection_name: str = Field(default="stock_knowledge")
    chroma_persist_directory: str = Field(default="runtime/chroma")

    market_data_cache_ttl_seconds: int = Field(default=300)
    prediction_model_path: str = Field(default="models/stock_trending_model.pt")
    prediction_sequence_length: int = Field(default=30)
    rag_enabled: bool = Field(default=False)
    logs_dir: str = Field(default="runtime/logs")

    def ensure_runtime_dirs(self) -> None:
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
