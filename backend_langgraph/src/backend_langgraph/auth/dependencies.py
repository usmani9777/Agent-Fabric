from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status

from backend_langgraph.auth.service import get_user_from_session
from backend_langgraph.core.config import get_settings
from backend_langgraph.db.clients import get_redis_client


def extract_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    parts = authorization.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


async def get_current_user(
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None),
) -> dict[str, Any]:
    token = x_session_token or extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")

    user = await get_user_from_session(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    return user


async def get_current_session_token(
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None),
) -> str:
    token = x_session_token or extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")
    return token


async def _enforce_rate_limit(request: Request, bucket: str, limit: int) -> None:
    client_host = request.client.host if request.client is not None else "unknown"
    key = f"rate:{bucket}:{client_host}"
    try:
        redis = get_redis_client()
        count = int(await redis.incr(key))
        if count == 1:
            await redis.expire(key, 60)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
    except HTTPException:
        raise
    except Exception:
        return


async def rate_limit_auth(request: Request) -> None:
    settings = get_settings()
    await _enforce_rate_limit(request, bucket="auth", limit=settings.auth_rate_limit_per_minute)


async def rate_limit_invoke(request: Request) -> None:
    settings = get_settings()
    await _enforce_rate_limit(request, bucket="invoke", limit=settings.invoke_rate_limit_per_minute)


async def require_admin_user(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if str(user.get("role", "user")) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user
