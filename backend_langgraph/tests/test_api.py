from fastapi.testclient import TestClient

from backend_langgraph.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200


def test_agent_invoke_returns_output() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/agent/invoke", json={"input": "hello"})

    assert response.status_code == 401
