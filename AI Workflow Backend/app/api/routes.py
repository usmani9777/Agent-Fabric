from flask import Blueprint, current_app, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health() -> tuple[dict, int]:
    manager = current_app.extensions["pipeline_manager"]
    return {
        "status": "ok",
        "cameras": manager.camera_sources,
        "active_threads": manager.active_thread_count(),
    }, 200


@api_bp.get("/flags")
def get_flags() -> tuple[dict, int]:
    manager = current_app.extensions["pipeline_manager"]
    return jsonify(manager.get_flags()), 200


@api_bp.post("/flags")
def update_flags() -> tuple[dict, int]:
    manager = current_app.extensions["pipeline_manager"]
    data = request.get_json(silent=True) or {}
    new_flags = manager.update_flags(data)
    return jsonify(new_flags), 200
