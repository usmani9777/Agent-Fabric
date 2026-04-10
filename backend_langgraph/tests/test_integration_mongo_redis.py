import asyncio
from typing import Any

import docker
import pytest
from fastapi.testclient import TestClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from backend_langgraph.core.config import get_settings
from backend_langgraph.db.clients import reset_clients


def _docker_available() -> bool:
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


@pytest.mark.integration
def test_agent_invoke_with_container_backed_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _docker_available():
        pytest.skip("Docker is required for integration tests")

    with MongoDbContainer("mongo:7") as mongo, RedisContainer("redis:7-alpine") as redis:
        monkeypatch.setenv("MONGO_URI", mongo.get_connection_url())
        monkeypatch.setenv("MONGO_DATABASE", "saynoma_integration")
        monkeypatch.setenv("REDIS_URL", redis.get_connection_url())
        monkeypatch.setenv("AUTO_BOOTSTRAP_INDEXES", "true")

        async def fake_call_tool(
            tool_name: str,
            arguments: dict[str, Any],
            session_token: str,
        ) -> Any:
            if tool_name == "refine_vague_prompt":
                return {"refined": f"Refined: {arguments['prompt']}"}
            if tool_name == "classify_intent":
                return {"intent": "rag"}
            if tool_name == "fetch_user_context":
                return {
                    "recent_memories": ["User prefers concise answers"],
                    "prompt_template": "Be concise.",
                }
            if tool_name == "rag_query":
                return [{"text": "RAG context result", "score": 2}]
            if tool_name == "store_user_memory":
                return {"status": "stored"}
            if tool_name == "summarize_text":
                return arguments["text"]
            return {}

        async def fake_groq_chat(
            system_prompt: str,
            user_prompt: str,
            temperature: float = 0.2,
        ) -> str:
            return "Final synthesized answer"

        import backend_langgraph.agent.graph as graph_module
        from backend_langgraph.agent.runner import get_compiled_graph

        monkeypatch.setattr(graph_module, "call_tool", fake_call_tool)
        monkeypatch.setattr(graph_module, "groq_chat", fake_groq_chat)

        get_settings.cache_clear()
        asyncio.run(reset_clients())
        get_compiled_graph.cache_clear()

        from backend_langgraph.main import create_app

        app = create_app()
        with TestClient(app) as client:
            reg = client.post(
                "/api/v1/auth/register",
                json={"email": "agent-int@example.com", "password": "super-secret-123"},
            )
            assert reg.status_code == 200
            token = reg.json()["session_token"]

            invoke = client.post(
                "/api/v1/agent/invoke",
                headers={"X-Session-Token": token},
                json={"input": "help", "refine_prompt": True},
            )
            assert invoke.status_code == 200
            payload = invoke.json()
            assert payload["selected_intent"] == "rag"
            assert payload["memory_written"] is True
            assert "Final synthesized answer" in payload["output"]

        get_settings.cache_clear()
        get_compiled_graph.cache_clear()
        asyncio.run(reset_clients())
