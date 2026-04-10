from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend_langgraph.auth.dependencies import (
    get_current_session_token,
    get_current_user,
    rate_limit_auth,
    require_admin_user,
)
from backend_langgraph.auth.service import (
    authenticate_user,
    count_users,
    create_session,
    invalidate_session,
    register_user,
    update_prompt_template,
)
from backend_langgraph.schemas.auth import (
    AdminUsersCountResponse,
    LoginRequest,
    PromptTemplateRequest,
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
    token: str = Depends(get_current_session_token),
) -> Response:
    await invalidate_session(token)
    return response


@router.get("/me", response_model=UserResponse)
async def me(user: dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=str(user["_id"]),
        email=str(user["email"]),
        role=str(user.get("role", "user")),
        prompt_template=str(user.get("prompt_template", "You are a strategic AI copilot.")),
    )


@router.put("/prompt-template", response_model=UserResponse)
async def set_prompt_template(
    payload: PromptTemplateRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    user_id = str(user["_id"])
    await update_prompt_template(user_id=user_id, prompt_template=payload.prompt_template)
    return UserResponse(
        user_id=user_id,
        email=str(user["email"]),
        role=str(user.get("role", "user")),
        prompt_template=payload.prompt_template,
    )


@router.get("/admin/users-count", response_model=AdminUsersCountResponse)
async def admin_users_count(
    _: dict[str, Any] = Depends(require_admin_user),
) -> AdminUsersCountResponse:
    return AdminUsersCountResponse(count=await count_users())
