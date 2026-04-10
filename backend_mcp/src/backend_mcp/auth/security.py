from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from backend_mcp.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return cast(bool, pwd_context.verify(plain_password, password_hash))


def new_session_token() -> str:
    return uuid4().hex


def sign_internal_jwt(payload: dict[str, Any]) -> str:
    settings = get_settings()
    content = {**payload, "iat": int(datetime.now(UTC).timestamp())}
    return cast(str, jwt.encode(content, settings.jwt_secret, algorithm=settings.jwt_algorithm))
