# AI Workflow Backend

This folder contains a clean, production-oriented backend implementation that is isolated from your original files.

The backend provides:

- Real-time multi-camera processing
- YOLO object detection and tracking
- Optional captioning pipeline
- REST APIs for health and runtime controls
- Socket.IO events for live frames and analytics
- Environment-driven configuration for deployment

## What This Backend Does

At a high level, the service reads one or more camera sources, processes frames with AI, and streams results to connected clients through WebSockets.

Each camera source runs in its own background worker thread. For each frame, the backend can:

- Detect objects
- Track objects between frames
- Count object classes
- Generate image captions (if enabled)

Results are emitted as Socket.IO events:

- Encoded video frame
- Detections
- Counts
- Caption text

## Project Structure

```text
backend_prod/
  app/
    __init__.py              # App factory, CORS, Socket.IO init, logging
    config.py                # Environment-based settings
    extensions.py            # Shared SocketIO extension instance
    api/
      routes.py              # REST endpoints (/api/health, /api/flags)
    services/
      pipeline_manager.py    # Camera thread lifecycle + frame processing orchestration
    sockets/
      handlers.py            # Socket.IO connect/update_flags handlers
    vision/
      stream.py              # Camera open/read/close helpers
      detection.py           # YOLO model loading + detection drawing
      tracking.py            # YOLO tracking + visualization + counting
      captioning.py          # Optional caption service wrapper
    templates/
      index.html             # Basic landing template (optional)
  run.py                     # Dev entrypoint
  wsgi.py                    # Production WSGI entrypoint
  gunicorn.conf.py           # Gunicorn runtime config
  requirements.txt
  .env.example
  docker-compose.yml
  Dockerfile
```

## How It Works

## 1) Startup Flow

1. Environment variables are loaded from `.env` (via `python-dotenv`).
2. `create_app()` builds Flask app, CORS policy, Socket.IO, and logging.
3. `PipelineManager` is created and stored on `app.extensions`.
4. API routes and Socket.IO handlers are registered.

## 2) Runtime Flow (Socket Client Connect)

1. Client connects to Socket.IO.
2. Backend ensures camera worker threads are started once.
3. Current flags are sent to the client.
4. Each camera worker loops over frames and emits updates.

## 3) Per-Frame Processing Pipeline

For each camera frame:

1. Read frame from source.
2. Check current runtime flags.
3. If detection is enabled:
   - Use tracking mode (if enabled) OR plain detection mode.
4. Optionally compute per-class counts.
5. Optionally generate captions every N frames.
6. JPEG-encode frame and emit socket events at `EMIT_FPS`.

## 4) Runtime Flag Updates

Flags can be changed via:

- REST: `POST /api/flags`
- Socket.IO: `update_flags`

The updated flags are broadcast so clients stay in sync.

## REST API

## Health and Control

- `GET /`
  - Basic service status JSON.

- `GET /api/health`
  - Returns health info, configured camera list, and active worker count.

- `GET /api/flags`
  - Returns the current runtime feature flags.

- `POST /api/flags`
  - Updates one flag or multiple flags.

Single flag update:

```json
{
  "flag": "detection",
  "value": false
}
```

Bulk update:

```json
{
  "detection": true,
  "tracking": false,
  "captioning": false,
  "counting": true
}
```

## Socket.IO Events

## Incoming from Client

- `update_flags`
  - Same payload options as `POST /api/flags`.

## Outgoing from Server

- `status`
  - Connection status message.

- `flags`
  - Current runtime flags.

- `frame_<camera_source>`
  - Base64 JPEG frame payload.

- `detections_<camera_source>`
  - List of detections/tracked items.

- `counts_<camera_source>`
  - Per-class counts.

- `caption_<camera_source>`
  - Caption text when captioning is enabled.

## Environment Configuration

Copy `.env.example` to `.env` and adjust values.

Key variables:

- `APP_HOST`, `APP_PORT`: bind host and port
- `LOG_LEVEL`: e.g. `INFO`, `DEBUG`
- `SECRET_KEY`: Flask secret key (set strong value in production)
- `CORS_ALLOWED_ORIGINS`: comma-separated allowed origins
- `CAMERA_SOURCES`: comma-separated camera sources (`0`, RTSP URL, file path)
- `YOLO_MODEL_PATH`: model file/path
- `EMIT_FPS`: emit rate per camera
- `DEFAULT_DETECTION`, `DEFAULT_TRACKING`, `DEFAULT_CAPTIONING`, `DEFAULT_COUNTING`: default feature toggles
- `SOCKETIO_ASYNC_MODE`: `threading` (default) or eventlet/gevent mode
- `MAX_UPLOAD_SIZE_BYTES`: Flask max request body
- `MAX_SOCKETIO_BUFFER_BYTES`: Socket.IO buffer cap

## Run Instructions

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

## Production (Gunicorn)

```powershell
gunicorn -c gunicorn.conf.py wsgi:app
```

Note: `gunicorn.conf.py` is currently tuned with 1 worker because camera/video pipelines are heavy and often GPU-bound.

## Docker

Build and run with Docker Compose:

```powershell
docker compose up --build
```

Container exposes port `5000`.

## Operational Notes

- Camera workers start on first socket connection, not on process boot.
- If a camera source fails to open, that camera thread exits while others continue.
- Captioning requires optional model/runtime availability; if unavailable, captioning is skipped safely.
- `frame_<camera_source>` event names include the raw source string. If your frontend needs safer keys, add a source-to-id mapping layer.

## Current Scope and Next Improvements

This backend is production-structured and deployable, but not yet fully enterprise-hardened.

Recommended next steps:

1. Add authentication and authorization for API and sockets.
2. Add request validation schemas (Pydantic/Marshmallow).
3. Add structured metrics and tracing (Prometheus/OpenTelemetry).
4. Add retry/reconnect strategy for unstable camera streams.
5. Add tests (unit + integration + socket event tests).
