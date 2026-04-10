from typing import cast
from uuid import uuid4

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return cast(bool, pwd_context.verify(plain_password, password_hash))


def new_session_token() -> str:
    return uuid4().hex
