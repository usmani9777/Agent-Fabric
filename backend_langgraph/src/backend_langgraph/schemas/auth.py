from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SessionResponse(BaseModel):
    session_token: str
    user_id: str
    email: EmailStr


class PromptTemplateRequest(BaseModel):
    prompt_template: str = Field(min_length=10, max_length=4000)


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    prompt_template: str


class AdminUsersCountResponse(BaseModel):
    count: int
