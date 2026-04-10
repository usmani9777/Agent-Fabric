from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

REQUEST_COUNTER = Counter(
    "backend_langgraph_requests_total",
    "Total requests served by backend_langgraph",
    ["endpoint"],
)


def record_request(endpoint: str) -> None:
    REQUEST_COUNTER.labels(endpoint=endpoint).inc()


def metrics_response() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
