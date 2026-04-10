import asyncio

import docker
import pytest
from fastapi.testclient import TestClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from backend_mcp.core.config import get_settings
from backend_mcp.db.clients import reset_clients


def _docker_available() -> bool:
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


@pytest.mark.integration
def test_auth_and_memory_tool_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _docker_available():
        pytest.skip("Docker is required for integration tests")

    with MongoDbContainer("mongo:7") as mongo, RedisContainer("redis:7-alpine") as redis:
        monkeypatch.setenv("MONGO_URI", mongo.get_connection_url())
        monkeypatch.setenv("MONGO_DATABASE", "saynoma_integration")
        monkeypatch.setenv("REDIS_URL", redis.get_connection_url())
        monkeypatch.setenv("AUTO_BOOTSTRAP_INDEXES", "true")

        get_settings.cache_clear()
        asyncio.run(reset_clients())

        from backend_mcp.main import create_app

        app = create_app()
        with TestClient(app) as client:
            reg = client.post(
                "/api/v1/auth/register",
                json={"email": "integration@example.com", "password": "super-secret-123"},
            )
            assert reg.status_code == 200
            token = reg.json()["session_token"]

            store = client.post(
                "/api/v1/tools/store_user_memory",
                headers={"X-Session-Token": token},
                json={
                    "arguments": {
                        "text": "Remember that project alpha uses Redis.",
                        "tags": ["project"],
                    }
                },
            )
            assert store.status_code == 200
            assert store.json()["result"]["status"] == "stored"

            search = client.post(
                "/api/v1/tools/long_term_user_memory_search",
                headers={"X-Session-Token": token},
                json={"arguments": {"query": "project alpha", "limit": 3}},
            )
            assert search.status_code == 200
            items = search.json()["result"]
            assert len(items) >= 1
            assert "project alpha" in items[0]["text"].lower()

        get_settings.cache_clear()
        asyncio.run(reset_clients())
