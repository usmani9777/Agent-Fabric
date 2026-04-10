# backend_langgraph

Production-grade LangGraph backend for Saynoma.

## Features

- FastAPI HTTP service for authenticated agent invocation
- LangGraph state graph with refine -> retrieve -> respond pipeline
- MCP-backed tool orchestration through `backend_mcp`
- Agent uses MCP tools for prompt refinement, intent classification, context retrieval, summarization, and memory write-back
- User prompt template management endpoint
- Session-based auth (`register`, `login`, `logout`, `me`)
- RBAC support (`role` field with admin-only analytics route)
- Redis-backed per-IP rate limiting for auth and invoke APIs
- MongoDB-backed user store and Redis-backed sessions
- Health and Prometheus metrics endpoints
- Structured JSON logging with `structlog`
- Request tracing via `X-Request-ID`
- Environment-based configuration via `.env`

## Quick Start

1. Install dependencies:
   - `uv sync`
2. Copy environment template:
   - `copy .env.example .env`
3. Run locally:
   - `uv run backend-langgraph`

Service defaults:

- API: `http://localhost:8080/api`
- Health: `http://localhost:8080/api/health`
- Invoke: `POST http://localhost:8080/api/v1/agent/invoke`
- PDF ingest: `POST http://localhost:8080/api/v1/knowledge/pdf-ingest`
- Metrics: `http://localhost:8080/api/metrics`
- Prompt template: `PUT http://localhost:8080/api/v1/auth/prompt-template`
- Admin users count: `GET http://localhost:8080/api/v1/auth/admin/users-count`

Example invoke payload:

```json
{
  "input": "Need strategy for onboarding docs",
  "refine_prompt": true
}
```

Use `X-Session-Token` or `Authorization: Bearer <session_token>` for authenticated routes.

## Quality Commands

- `uv run pytest`
- `uv run pytest -m integration` (requires Docker)
- `uv run ruff check .`
- `uv run mypy src`

## Database Bootstrap

- One-time/manual index bootstrap:
  - `uv run backend-langgraph-bootstrap-db`
- Or set `AUTO_BOOTSTRAP_INDEXES=true` to auto-create indexes on service startup.

## Container

- Build: `docker build -t backend-langgraph .`
- Run: `docker run --rm -p 8080:8080 backend-langgraph`
