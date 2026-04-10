from app import create_app
from app.extensions import socketio


app, _pipeline_manager = create_app()


if __name__ == "__main__":
    from app.config import Settings

    cfg = Settings.from_env()
    socketio.run(app, host=cfg.app_host, port=cfg.app_port)
