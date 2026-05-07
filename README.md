# Stock Agent AI

Production-oriented starter for a hybrid stock analysis system using FastAPI, LangGraph, LangChain, Ollama, Redis, PostgreSQL, Docker, and a local PyTorch prediction model.

## Components

- `apps/api`: HTTP API for synchronous analysis requests
- `apps/worker`: Redis-backed background worker
- `agents`: Single-responsibility agent implementations
- `graph`: LangGraph state and orchestration builder
- `services`: Market data, indicators, LLM, ML model, storage, and config services
- `db`: SQLAlchemy models and bootstrap SQL
- `rag`: Retrieval contracts for future RAG integration
- `models/stock_trending_model.pt`: expected local PyTorch artifact path

## Run

1. Copy `.env.example` to `.env` and adjust values.
2. Add `models/stock_trending_model.pt`.
3. Start services:

```bash
docker compose up --build
```

4. Analyze a symbol:

```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"lookback_days\":180}"
```

## Notes

- The ML prediction signal is auxiliary and does not decide trades on its own.
- Technical indicators are deterministic and never delegated to the LLM.
- `fundamental_service.py` is a placeholder estimator and should be replaced with a real provider before live usage.
- The prediction service falls back cleanly when the `.pt` artifact is missing.
