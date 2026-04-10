from flask_socketio import emit


def register_socket_handlers(socketio, pipeline_manager) -> None:
    @socketio.on("connect")
    def handle_connect():
        pipeline_manager.ensure_started()
        emit("flags", pipeline_manager.get_flags())
        emit("status", {"msg": "connected"})

    @socketio.on("update_flags")
    def handle_update_flags(data):
        updated = pipeline_manager.update_flags(data if isinstance(data, dict) else {})
        emit("flags", updated, broadcast=True)
