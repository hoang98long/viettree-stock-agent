"""Ollama LLM factory."""

from langchain_ollama import ChatOllama

from services.config import Settings


class OllamaClientFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_reasoning_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_reasoning_model,
            temperature=0,
        )
