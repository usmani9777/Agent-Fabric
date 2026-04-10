# Agent Fabric

Agent Fabric is a two-service AI backend platform built with Python and managed with `uv`.

## What This Project Contains

- `backend_mcp`: the tool and knowledge backend (MCP server + HTTP APIs).
- `backend_langgraph`: the orchestrator backend (LangGraph agent + user-facing AI APIs).
- `mongo`: primary persistent data store.
- `redis`: session, cache, and rate-limiter store.

## Architecture Overview

The runtime topology is:

1. Client calls `backend_langgraph` API.
2. LangGraph service authenticates user session (Redis + Mongo user lookup).
3. LangGraph graph decides which MCP tools are needed.
4. LangGraph calls MCP tool endpoints.
5. MCP backend executes tools using Mongo/Redis/Groq and returns results.
6. LangGraph composes final response and writes conversation memory back.

## Service Responsibilities

### backend_mcp

- Hosts MCP tool server endpoint.
- Exposes HTTP routes for auth and tool invocation.
- Implements 10 MCP tools:
  1. `pdf_ingestion`
  2. `rag_query`
  3. `wiki_search`
  4. `long_term_user_memory_search`
  5. `refine_vague_prompt`
  6. `web_search`
  7. `summarize_text`
  8. `store_user_memory`
  9. `fetch_user_context`
  10. `classify_intent`
- Owns document chunks and long-term memory persistence.
- Handles tool-level rate limiting and request tracing.

### backend_langgraph

- Exposes user-facing API endpoints.
- Runs LangGraph pipeline:
  - refine prompt
  - hydrate user context
  - classify/retrieve context
  - generate response
  - store memory
- Calls MCP backend tools via HTTP.
- Provides authenticated PDF ingest endpoint that delegates to MCP.
- Applies auth/invoke rate limiting and request tracing.

## Security and Access Model

Both services implement:

- Session authentication with token in:
  - `X-Session-Token`
  - or `Authorization: Bearer <token>`
- Redis-backed session TTL.
- RBAC with roles (`user`, `admin`).
- Admin-only analytics endpoint:
  - `GET /api/v1/auth/admin/users-count`
- Per-IP rate limiting stored in Redis.
- Structured logs and `X-Request-ID` propagation.

## Data Model (High-Level)

Mongo collections:

- `users`
  - `email`, `password_hash`, `role`, `prompt_template`, timestamps
- `rag_chunks`
  - `user_id`, `source`, `file_name`, `chunk_index`, `text`, timestamp
- `user_memories`
  - `user_id`, `text`, `tags`, timestamp

Redis keys:

- `session:<token>` -> user id
- `rag:<user>:<query>:<limit>` -> cached RAG result
- `rate:<bucket>:<client_ip>` -> rate counter

## API Surface Summary

### backend_mcp

- Health: `GET /api/health`
- Metrics: `GET /api/metrics`
- MCP app mount: `/mcp`
- Auth:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
  - `GET /api/v1/auth/admin/users-count`
- Tools:
  - `POST /api/v1/tools/{tool_name}` (session auth)
  - `POST /api/v1/tools/{tool_name}/internal` (internal API key)

### backend_langgraph

- Health: `GET /api/health`
- Metrics: `GET /api/metrics`
- Auth:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
  - `PUT /api/v1/auth/prompt-template`
  - `GET /api/v1/auth/admin/users-count`
- Agent:
  - `POST /api/v1/agent/invoke`
- Knowledge:
  - `POST /api/v1/knowledge/pdf-ingest`

## Environment Variables

### backend_mcp required/important

- `MONGO_URI`
- `MONGO_DATABASE`
- `REDIS_URL`
- `SESSION_TTL_SECONDS`
- `JWT_SECRET`
- `INTERNAL_API_KEY`
- `GROQ_API_KEY` (required for live Groq calls)
- `BOOTSTRAP_ADMIN_EMAIL` (optional admin bootstrap)
- `AUTH_RATE_LIMIT_PER_MINUTE`
- `TOOL_RATE_LIMIT_PER_MINUTE`
- `AUTO_BOOTSTRAP_INDEXES`

### backend_langgraph required/important

- `MONGO_URI`
- `MONGO_DATABASE`
- `REDIS_URL`
- `SESSION_TTL_SECONDS`
- `MCP_BACKEND_BASE_URL`
- `GROQ_API_KEY` (required for live Groq calls)
- `BOOTSTRAP_ADMIN_EMAIL` (optional admin bootstrap)
- `AUTH_RATE_LIMIT_PER_MINUTE`
- `INVOKE_RATE_LIMIT_PER_MINUTE`
- `AUTO_BOOTSTRAP_INDEXES`

See service-local examples:

- `backend_mcp/.env.example`
- `backend_langgraph/.env.example`

## Setup and Run

### Local without Docker

1. `cd backend_mcp`
2. `uv sync`
3. `copy .env.example .env`
4. `uv run backend-mcp`

In a second terminal:

1. `cd backend_langgraph`
2. `uv sync`
3. `copy .env.example .env`
4. `uv run backend-langgraph`

### Docker Compose stack

From workspace root:

- `docker compose up --build`

This starts:

- `backend-mcp` on `8081`
- `backend-langgraph` on `8080`
- `mongo` on `27017`
- `redis` on `6379`

## Database Bootstrap and Indexes

Manual bootstrap commands:

- MCP: `cd backend_mcp; uv run backend-mcp-bootstrap-db`
- LangGraph: `cd backend_langgraph; uv run backend-langgraph-bootstrap-db`

Or enable automatic bootstrap on startup with:

- `AUTO_BOOTSTRAP_INDEXES=true`

## Testing and Quality

Per backend:

- Lint: `uv run ruff check .`
- Type-check: `uv run mypy src`
- Unit tests: `uv run pytest`
- Integration tests: `uv run pytest -m integration` (requires Docker)

## CI/CD

GitHub Actions workflow:

- `.github/workflows/ci.yml`

It runs:

1. Ruff
2. Mypy
3. Pytest
4. Integration marker tests

## One-Command Deploy Check

Run from workspace root:

- `powershell -ExecutionPolicy Bypass -File ./ops/deploy-check.ps1`

What it does:

1. Starts compose stack.
2. Waits for health endpoints.
3. Bootstraps indexes on both services.
4. Runs smoke auth + invoke flow.
5. Prints runtime summary.

## Caches and Build Artifacts

Common generated folders:

- `.mypy_cache/`
- `.ruff_cache/`
- `.pytest_cache/`
- `__pycache__/`

These are safe to delete and are recreated automatically.

Cleanup (PowerShell):

- `Get-ChildItem -Force -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force; Remove-Item -Recurse -Force .mypy_cache,.ruff_cache,.pytest_cache -ErrorAction SilentlyContinue`

## Repository Notes

- Git repository is initialized on branch `main`.
- The project is validated locally with lint/type/tests passing.
- Integration tests are Docker-gated and skip automatically when Docker is unavailable.
