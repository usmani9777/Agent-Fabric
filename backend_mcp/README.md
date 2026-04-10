# backend_mcp

Production-grade MCP backend for Saynoma.

## Features

- FastAPI HTTP service with health and Prometheus metrics endpoints
- Mounted MCP server app for tool invocation at `/mcp`
- 10 production MCP tools (RAG, PDF ingestion, memory, web/wiki, Groq refinement)
- Session-based auth (`register`, `login`, `logout`, `me`)
- RBAC support (`role` field with admin-only analytics route)
- Redis-backed per-IP rate limiting for auth and tool APIs
- MongoDB for users, memory, and document chunks
- Redis for sessions and RAG cache
- Structured JSON logging with `structlog`
- Request tracing via `X-Request-ID`
- Environment-based configuration via `.env`
- Test, lint, and type-check support

## Quick Start

1. Install dependencies:
   - `uv sync`
2. Copy environment template:
   - `copy .env.example .env`
3. Run locally:
   - `uv run backend-mcp`

Service defaults:

- API: `http://localhost:8081/api`
- Health: `http://localhost:8081/api/health`
- Metrics: `http://localhost:8081/api/metrics`
- MCP: `http://localhost:8081/mcp`
- Auth register: `POST /api/v1/auth/register`
- Auth login: `POST /api/v1/auth/login`
- Admin users count: `GET /api/v1/auth/admin/users-count`
- Tool invoke: `POST /api/v1/tools/{tool_name}`

## MCP Tools

1. `pdf_ingestion`
2. `rag_query`
3. `wiki_search`
4. `long_term_user_memory_search`
5. `refine_vague_prompt` (Groq)
6. `web_search`
7. `summarize_text` (Groq)
8. `store_user_memory`
9. `fetch_user_context`
10. `classify_intent`

## Quality Commands

- `uv run pytest`
- `uv run pytest -m integration` (requires Docker)
- `uv run ruff check .`
- `uv run mypy src`

## Database Bootstrap

- One-time/manual index bootstrap:
  - `uv run backend-mcp-bootstrap-db`
- Or set `AUTO_BOOTSTRAP_INDEXES=true` to auto-create indexes on service startup.

## Container

- Build: `docker build -t backend-mcp .`
- Run: `docker run --rm -p 8081:8081 backend-mcp`
