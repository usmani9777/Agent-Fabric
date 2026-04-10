from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, TEXT

from backend_mcp.db.clients import get_database


async def ensure_indexes() -> None:
    db = get_database()

    await db["users"].create_index([("email", ASCENDING)], unique=True, name="uniq_email")
    await db["users"].create_index([("created_at", DESCENDING)], name="users_created_at_desc")

    await db["rag_chunks"].create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        name="rag_user_created_idx",
    )
    await db["rag_chunks"].create_index(
        [
            ("user_id", ASCENDING),
            ("source", ASCENDING),
            ("file_name", ASCENDING),
            ("chunk_index", ASCENDING),
        ],
        name="rag_dedup_lookup_idx",
    )
    await db["rag_chunks"].create_index([("text", TEXT)], name="rag_text_idx")

    await db["user_memories"].create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        name="memory_user_created_idx",
    )
    await db["user_memories"].create_index([("text", TEXT)], name="memory_text_idx")
