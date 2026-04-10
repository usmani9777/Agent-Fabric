from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from backend_mcp.auth.dependencies import get_current_user, rate_limit_auth, require_admin_user
from backend_mcp.auth.service import (
    authenticate_user,
    count_users,
    create_session,
    invalidate_session,
    register_user,
)
from backend_mcp.schemas.auth import (
    AdminUsersCountResponse,
    LoginRequest,
    RegisterRequest,
    SessionResponse,
    UserResponse,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"], dependencies=[Depends(rate_limit_auth)])


@router.post("/register", response_model=SessionResponse)
async def register(payload: RegisterRequest) -> SessionResponse:
    try:
        user = await register_user(payload.email, payload.password)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    token = await create_session(user)
    return SessionResponse(session_token=token, user_id=str(user["_id"]), email=user["email"])


@router.post("/login", response_model=SessionResponse)
async def login(payload: LoginRequest) -> SessionResponse:
    try:
        user = await authenticate_user(payload.email, payload.password)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error

    token = await create_session(user)
    return SessionResponse(session_token=token, user_id=str(user["_id"]), email=user["email"])


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    user: dict[str, Any] = Depends(get_current_user),
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None),
) -> Response:
    token = x_session_token
    if token is None and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", maxsplit=1)[1]
    if token is not None:
        await invalidate_session(token)
    return response


@router.get("/me", response_model=UserResponse)
async def me(user: dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=str(user["_id"]),
        email=str(user["email"]),
        role=str(user.get("role", "user")),
        prompt_template=str(user.get("prompt_template", "You are a precise assistant.")),
    )


@router.get("/admin/users-count", response_model=AdminUsersCountResponse)
async def admin_users_count(
    _: dict[str, Any] = Depends(require_admin_user),
) -> AdminUsersCountResponse:
    return AdminUsersCountResponse(count=await count_users())
