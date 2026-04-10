import os
from dataclasses import dataclass


def _parse_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(slots=True)
class Settings:
    app_host: str
    app_port: int
    log_level: str
    secret_key: str
    cors_allowed_origins: list[str]
    camera_sources: list[str]
    yolo_model_path: str
    emit_fps: int
    default_detection: bool
    default_stream: bool
    default_tracking: bool
    default_captioning: bool
    default_counting: bool
    socketio_async_mode: str
    max_upload_size_bytes: int
    max_socketio_buffer_size_bytes: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_host=os.getenv("APP_HOST", "0.0.0.0"),
            app_port=_parse_int(os.getenv("APP_PORT"), 5000),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
            cors_allowed_origins=_parse_list(
                os.getenv("CORS_ALLOWED_ORIGINS"), ["http://localhost:4200", "http://127.0.0.1:4200"]
            ),
            camera_sources=_parse_list(os.getenv("CAMERA_SOURCES"), ["0"]),
            yolo_model_path=os.getenv("YOLO_MODEL_PATH", "yolov8n.pt"),
            emit_fps=_parse_int(os.getenv("EMIT_FPS"), 10),
            default_detection=_parse_bool(os.getenv("DEFAULT_DETECTION"), True),
            default_stream=_parse_bool(os.getenv("DEFAULT_STREAM"), True),
            default_tracking=_parse_bool(os.getenv("DEFAULT_TRACKING"), True),
            default_captioning=_parse_bool(os.getenv("DEFAULT_CAPTIONING"), False),
            default_counting=_parse_bool(os.getenv("DEFAULT_COUNTING"), True),
            socketio_async_mode=os.getenv("SOCKETIO_ASYNC_MODE", "threading"),
            max_upload_size_bytes=_parse_int(os.getenv("MAX_UPLOAD_SIZE_BYTES"), 5 * 1024 * 1024 * 1024),
            max_socketio_buffer_size_bytes=_parse_int(
                os.getenv("MAX_SOCKETIO_BUFFER_BYTES"),
                1024 * 1024 * 1024,
            ),
        )
