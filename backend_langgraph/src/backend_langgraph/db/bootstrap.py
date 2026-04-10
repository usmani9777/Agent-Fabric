from __future__ import annotations

import asyncio

from backend_langgraph.db.clients import lifespan_clients
from backend_langgraph.db.indexes import ensure_indexes


async def _bootstrap() -> None:
    async with lifespan_clients():
        await ensure_indexes()


def main() -> None:
    asyncio.run(_bootstrap())


if __name__ == "__main__":
    main()
