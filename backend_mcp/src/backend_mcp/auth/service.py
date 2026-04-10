from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from bson import ObjectId

from backend_mcp.auth.security import hash_password, new_session_token, verify_password
from backend_mcp.core.config import get_settings
from backend_mcp.db.clients import get_database, get_redis_client


async def register_user(email: str, password: str) -> dict[str, Any]:
    db = get_database()
    users = db["users"]

    existing = await users.find_one({"email": email})
    if existing is not None:
        raise ValueError("Email already registered")

    settings = get_settings()
    role = (
        "admin"
        if settings.bootstrap_admin_email and email == settings.bootstrap_admin_email
        else "user"
    )

    now = datetime.now(UTC)
    payload = {
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "prompt_template": "You are a precise assistant.",
        "created_at": now,
        "updated_at": now,
    }
    result = await users.insert_one(payload)
    return {
        "_id": result.inserted_id,
        "email": email,
        "role": role,
        "prompt_template": payload["prompt_template"],
    }


async def authenticate_user(email: str, password: str) -> dict[str, Any]:
    db = get_database()
    user = await db["users"].find_one({"email": email})
    if user is None:
        raise ValueError("Invalid credentials")

    password_hash = str(user.get("password_hash", ""))
    if not verify_password(password, password_hash):
        raise ValueError("Invalid credentials")

    return cast(dict[str, Any], user)


async def create_session(user: dict[str, Any]) -> str:
    settings = get_settings()
    token = new_session_token()
    key = f"session:{token}"
    user_id = str(user["_id"])
    await get_redis_client().setex(key, settings.session_ttl_seconds, user_id)
    return token


async def get_user_from_session(token: str) -> dict[str, Any] | None:
    key = f"session:{token}"
    user_id = await get_redis_client().get(key)
    if user_id is None:
        return None

    db = get_database()
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    return user


async def invalidate_session(token: str) -> None:
    await get_redis_client().delete(f"session:{token}")


async def count_users() -> int:
    return int(await get_database()["users"].count_documents({}))
