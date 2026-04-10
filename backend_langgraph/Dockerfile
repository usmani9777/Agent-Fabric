FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv==0.10.4

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src ./src

EXPOSE 8080

CMD ["uv", "run", "backend-langgraph"]
