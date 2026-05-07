# Stock Agent AI - AI Engineering Guide

This file is the working guide for AI-assisted development in this repository. It serves the same role as a `CLAUDE.md` or repo-local agent guide: define architecture constraints, implementation rules, and review standards so Codex can make changes without drifting the system.

Use this guide as the default operating contract unless the user gives a newer explicit instruction.

## Goal

Build and evolve a production-oriented multi-agent stock analysis system that:

- analyzes stock market data with deterministic indicators and a local ML model
- produces `BUY`, `SELL`, or `HOLD`
- returns confidence, alerts, and reasoning
- is ready for future backtesting and RAG integration

Primary stack:

- Python
- FastAPI
- LangGraph
- LangChain
- Ollama
- Redis
- PostgreSQL
- Docker

## Core Principles

- Keep business logic deterministic where possible.
- Use LLMs for reasoning, summarization, and explanation only.
- Keep each agent single-responsibility.
- Keep orchestration explicit in LangGraph.
- Prefer composable services over large agent classes.
- Design for observability, retries, and partial failure.
- Optimize for maintainability before novelty.

## Architecture Principles

- The system is hybrid:
  - agentic orchestration for workflow control
  - deterministic analytics for technical and rule-based scoring
  - local ML model for directional signal support
  - RAG-ready interfaces for future knowledge augmentation
- The graph is the source of truth for execution order.
- Agents should return partial state updates only.
- External I/O belongs in service layers, not in decision logic.
- All decision outputs must be reproducible from input state plus validated LLM responses.
- Shared infrastructure concerns such as config, caching, persistence, and logging must live under `services/` or `db/`, not inside agent files.

## Coding Standards

- Use Python 3.12+ style and type hints throughout.
- Prefer small modules with one clear responsibility.
- Use `TypedDict`, dataclasses, or Pydantic where structure matters.
- Avoid hidden global state.
- Avoid side effects at import time.
- Keep functions short and explicit.
- Raise specific exceptions for validation and runtime failures.
- Validate all external input at the boundary.
- Add `TODO` comments only for real follow-up work, not placeholders without context.
- Do not introduce broad abstractions unless they remove concrete duplication or complexity.

## LangGraph Rules

- Use `TypedDict` state for the graph contract.
- Keep state keys stable. Do not rename keys casually.
- Each node must read from state and return a partial state dict.
- Do not mutate unrelated state fields inside an agent.
- The graph topology must remain easy to inspect.
- Prefer fan-out from `data_agent` into analysis agents, then converge into `decision_agent`.
- Keep branching deterministic unless there is a clear performance or product reason.
- Do not hide orchestration rules inside service code.
- If a new agent is added, update:
  - graph topology
  - state definition
  - tests
  - this guide if the role changes system behavior

## State Management Rules

LangGraph state must include:

- `symbol`
- `price_data`
- `indicators`
- `fundamentals`
- `sentiment`
- `prediction`
- `decision`
- `alerts`
- `metadata`

Rules:

- Treat state as a contract between agents.
- Keep each top-level state field semantically narrow.
- `metadata` is for execution context, flags, timing, provenance, and run annotations.
- Do not overload `metadata` with domain results that deserve first-class fields.
- `price_data` should contain normalized serializable data only.
- State values must be JSON-serializable by default unless a specific internal graph-only object is justified.
- Avoid storing heavyweight raw objects like DataFrames or DB sessions in the long-lived state.

## Agent Responsibilities

### `data_agent`

- Fetch and normalize market data.
- No LLM usage.
- No investment reasoning.
- Must return clean price history and provenance metadata.

### `technical_agent`

- Compute indicators using deterministic libraries such as `pandas-ta`.
- No LLM usage.
- No API calls unless the agent is explicitly extended for internal data enrichment.
- Must never compute indicators by prompting a model.

### `fundamental_agent`

- Build issuer-level fundamental snapshots or derived fundamental signals.
- Prefer deterministic rules over narrative output.
- If upstream data is unavailable, return explicit fallback status.

### `sentiment_agent`

- Use LLM reasoning with short, constrained prompts.
- Must return validated structured output.
- Should not decide trades directly.

### `prediction_agent`

- Load and run the local PyTorch `.pt` model.
- Emit directional prediction plus confidence and raw metadata.
- The prediction is an input signal only.
- Do not fetch remote model artifacts at runtime.

### `decision_agent`

- Combine all prior signals into final action and reasoning.
- No external API access.
- No indicator computation.
- No market data fetching.
- Must produce strict structured output.
- Must treat ML output as one signal among several, not the final authority.

### `alert_agent`

- Convert final decision and notable signals into actionable alerts.
- Keep alert generation deterministic.
- Separate alert severity from trade decision.

## Prompt Engineering Rules

- Keep prompts short.
- Always state the output schema.
- Prefer strict JSON outputs.
- Constrain the model to the minimum needed context.
- Ask for explanation, not invention.
- Do not ask the LLM to calculate technical indicators or numerical signals already available in code.
- Validate every LLM response before using it.
- Provide fallback behavior when parsing fails.
- Avoid multi-paragraph prompts unless the task actually requires more context.

Prompt template guidance:

- system prompt:
  - define role narrowly
  - define exact output shape
  - forbid markdown unless needed
- user prompt:
  - include only relevant signals
  - pass normalized values
  - avoid prose-heavy context dumps

## ML Integration Rules

- Prediction uses a local PyTorch `.pt` artifact.
- Model inference must be isolated in `services/prediction_model.py` or equivalent.
- Do not bury model loading inside unrelated agents.
- Feature generation must be deterministic and versionable.
- Missing model artifacts must fail clearly or use an explicit fallback path.
- Log model version or model path for every run.
- Do not let ML inference directly override deterministic risk controls.
- Keep input feature shape, sequence length, and label assumptions documented in code.
- Future model retraining code should remain separate from inference runtime.

## Anti-Patterns

Do not do any of the following:

- compute RSI, MACD, or similar indicators with an LLM
- fetch external APIs inside `decision_agent`
- combine data fetching, reasoning, and persistence in one agent
- return free-form model text without validation
- pass raw DataFrames through every layer when a serialized form is enough
- hide important business rules inside prompt wording alone
- treat the ML model as the final trading decision
- write oversized agent classes that own multiple concerns
- build graph behavior implicitly through side effects
- add cross-cutting logic directly into API route handlers

## File Organization Rules

Project layout:

- `apps/api/`: FastAPI app, routes, schemas, dependency wiring
- `apps/worker/`: async workers and queue consumers
- `agents/`: graph node implementations only
- `graph/`: state definitions and LangGraph builder
- `services/`: reusable domain and infrastructure services
- `models/`: local model artifacts and model notes
- `db/`: ORM models, SQL bootstrap, repositories, sessions
- `rag/`: future retrieval interfaces and implementations
- `configs/`: future split configuration modules if needed

Rules:

- Keep route handlers thin.
- Keep agents thin.
- Put reusable domain logic in `services/`.
- Put persistence logic in `db/` or storage services.
- Do not create circular dependencies between `agents/`, `services/`, and `graph/`.
- If a file exceeds a reasonable single-purpose size, split it by concern.

## Logging Strategy

- Use structured, consistent application logs.
- Log at least:
  - run start
  - run end
  - symbol
  - agent failures
  - fallback conditions
  - model loading status
  - persistence failures
- Never log secrets.
- Avoid logging entire raw payloads unless needed for debugging and explicitly safe.
- Include symbol and execution context in logs wherever possible.
- LLM parsing failures should be logged with enough context to debug, but not with excessive noisy dumps.

Recommended approach:

- module-level logger per file
- centralized logging config
- consistent message keys
- future-ready path for JSON logs in containers

## Testing Strategy

Minimum expectations:

- test each agent independently
- test graph execution end to end
- mock LLM calls
- mock remote market data providers
- test structured output validation and fallback logic
- test prediction fallback when model file is missing
- test persistence and queue integration separately

Recommended test layers:

### Unit tests

- indicator calculations
- decision scoring
- prompt parsing
- model feature preparation
- repository methods

### Integration tests

- API request to graph execution
- Redis-backed queue flow
- PostgreSQL persistence
- Docker-compose local startup sanity

### Regression tests

- state key stability
- decision schema stability
- graph topology assumptions

## Docker Workflow

- Use Docker for local parity with deployment.
- Keep API, worker, Redis, PostgreSQL, and Ollama as separate services.
- Build reproducible images with pinned dependencies where practical.
- Prefer environment variables over hardcoded deployment values.
- Mount model artifacts and config explicitly.
- Do not assume Ollama models are pre-pulled; bootstrap them deliberately.

Expected workflow:

1. update `.env`
2. ensure `models/stock_trending_model.pt` exists
3. run `docker compose up --build`
4. verify API health and dependencies
5. test one end-to-end analysis request

## Review Checklist For Codex

Before finalizing a change, verify:

- architecture boundaries still hold
- state keys remain consistent
- agents remain single-responsibility
- no LLM is used for deterministic numeric computation
- `decision_agent` performs no external fetching
- ML output is auxiliary only
- new files are placed in the right package
- errors and fallbacks are explicit
- tests cover the changed behavior proportionally

## Future Scalability Notes

Plan for these extensions without blocking current delivery:

- backtesting engine separated from live inference path
- batch analysis for multi-symbol workflows
- richer alert routing and notification channels
- RAG-backed research summaries
- memory or history-aware signal comparison
- model registry and artifact versioning
- async parallel execution for expensive non-dependent nodes
- observability stack with metrics and traces
- role-based API auth and audit logging

Keep future scaling work additive. Do not entangle today’s runtime graph with speculative features unless there is a clear interface boundary.

## How Codex Should Behave In This Repo

- Read the relevant files before editing.
- Prefer local patterns already established in the repo.
- Make narrowly scoped changes.
- Preserve graph and state contracts.
- When adding a new capability, update code, docs, and tests together.
- Call out blockers clearly when external assets are missing, especially:
  - PyTorch model files
  - Ollama models
  - database connectivity
  - market data provider issues

If a user request conflicts with this guide, follow the user’s explicit request and preserve as much of the architecture discipline as possible.
