from __future__ import annotations

from pymongo import ASCENDING, DESCENDING

from backend_langgraph.db.clients import get_database


async def ensure_indexes() -> None:
    db = get_database()
    await db["users"].create_index([("email", ASCENDING)], unique=True, name="uniq_email")
    await db["users"].create_index([("created_at", DESCENDING)], name="users_created_at_desc")
