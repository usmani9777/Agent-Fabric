import logging

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .api.routes import api_bp
from .config import Settings
from .extensions import socketio
from .services.pipeline_manager import PipelineManager
from .sockets.handlers import register_socket_handlers


def create_app(settings: Settings | None = None) -> tuple[Flask, PipelineManager]:
    load_dotenv()
    cfg = settings or Settings.from_env()

    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = cfg.secret_key
    app.config["MAX_CONTENT_LENGTH"] = cfg.max_upload_size_bytes

    CORS(
        app,
        resources={r"/api/*": {"origins": cfg.cors_allowed_origins}},
        supports_credentials=True,
    )

    socketio.init_app(
        app,
        cors_allowed_origins=cfg.cors_allowed_origins,
        async_mode=cfg.socketio_async_mode,
        max_http_buffer_size=cfg.max_socketio_buffer_size_bytes,
    )

    _configure_logging(app, cfg)

    pipeline_manager = PipelineManager(cfg)
    app.extensions["pipeline_manager"] = pipeline_manager

    app.register_blueprint(api_bp)

    @app.get("/")
    def index():
        return {"service": "ai-workflow-backend", "status": "ok"}, 200

    register_socket_handlers(socketio, pipeline_manager)

    return app, pipeline_manager


def _configure_logging(app: Flask, cfg: Settings) -> None:
    level = getattr(logging, cfg.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.logger.setLevel(level)
