from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "saynoma-langgraph-backend"
    version: str = "0.1.0"
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    workers: int = Field(default=2, alias="WORKERS")
    debug: bool = Field(default=False, alias="DEBUG")
    reload: bool = Field(default=False, alias="RELOAD")
    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGO_URI")
    mongo_database: str = Field(default="saynoma", alias="MONGO_DATABASE")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    session_ttl_seconds: int = Field(default=86400, alias="SESSION_TTL_SECONDS")
    mcp_backend_base_url: str = Field(default="http://localhost:8081", alias="MCP_BACKEND_BASE_URL")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    auto_bootstrap_indexes: bool = Field(default=False, alias="AUTO_BOOTSTRAP_INDEXES")
    bootstrap_admin_email: str = Field(default="", alias="BOOTSTRAP_ADMIN_EMAIL")
    auth_rate_limit_per_minute: int = Field(default=60, alias="AUTH_RATE_LIMIT_PER_MINUTE")
    invoke_rate_limit_per_minute: int = Field(default=90, alias="INVOKE_RATE_LIMIT_PER_MINUTE")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
