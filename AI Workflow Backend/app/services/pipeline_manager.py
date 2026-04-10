import base64
import threading
import time
from collections import Counter

import cv2

from app.config import Settings
from app.extensions import socketio
from app.vision.captioning import CaptionService
from app.vision.detection import detect_objects, draw_detections, load_yolo_model
from app.vision.stream import close_camera, open_camera, read_frame
from app.vision.tracking import draw_tracks, track_objects


class PipelineManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.camera_sources = settings.camera_sources
        self.flags = {
            "detection": settings.default_detection,
            "stream": settings.default_stream,
            "tracking": settings.default_tracking,
            "captioning": settings.default_captioning,
            "counting": settings.default_counting,
        }
        self._threads: dict[str, threading.Thread] = {}
        self._stop_events: dict[str, threading.Event] = {}
        self._started = False
        self._lock = threading.Lock()

    def ensure_started(self) -> None:
        with self._lock:
            if self._started:
                return
            for source in self.camera_sources:
                stop_event = threading.Event()
                self._stop_events[source] = stop_event
                t = threading.Thread(target=self._run_camera, args=(source, stop_event), daemon=True)
                self._threads[source] = t
                t.start()
            self._started = True

    def update_flags(self, data: dict) -> dict[str, bool]:
        with self._lock:
            if "flag" in data and "value" in data:
                flag_name = data["flag"]
                if flag_name in self.flags:
                    self.flags[flag_name] = bool(data["value"])
            else:
                for key in self.flags:
                    if key in data:
                        self.flags[key] = bool(data[key])
            return dict(self.flags)

    def get_flags(self) -> dict[str, bool]:
        with self._lock:
            return dict(self.flags)

    def active_thread_count(self) -> int:
        return sum(1 for t in self._threads.values() if t.is_alive())

    def _run_camera(self, source: str, stop_event: threading.Event) -> None:
        cap = open_camera(source)
        if cap is None:
            return

        yolo_model = load_yolo_model(self.settings.yolo_model_path)
        captioner = CaptionService() if self.settings.default_captioning else None

        last_emit = 0.0
        frame_count = 0

        try:
            while not stop_event.is_set():
                frame = read_frame(cap)
                if frame is None:
                    time.sleep(0.05)
                    continue

                frame_count += 1
                flags = self.get_flags()
                send_caption = None
                send_counts = {}
                send_detections = []

                if flags.get("detection"):
                    if flags.get("tracking"):
                        tracked = track_objects(
                            yolo_model,
                            frame,
                            conf_threshold=0.7,
                            counting=flags.get("counting", False),
                        )
                        if len(tracked) == 7:
                            bboxes, class_ids, track_ids, scores, frame, class_names, counts = tracked
                            send_counts = counts
                        else:
                            bboxes, class_ids, track_ids, scores, frame, class_names = tracked
                        frame = draw_tracks(frame, bboxes, class_ids, track_ids, scores, class_names)
                        send_detections = [
                            {"id": tid, "label": class_names[cid], "score": float(scr)}
                            for tid, cid, scr in zip(track_ids, class_ids, scores)
                        ]
                    else:
                        bboxes, class_ids, scores, frame, class_names = detect_objects(
                            yolo_model,
                            frame,
                            conf_threshold=0.5,
                        )
                        frame = draw_detections(frame, bboxes, class_ids, scores, class_names)
                        if flags.get("counting"):
                            send_counts = dict(Counter([class_names[cid] for cid in class_ids]))
                        send_detections = [
                            {"label": class_names[cid], "score": float(scr)}
                            for cid, scr in zip(class_ids, scores)
                        ]

                if flags.get("captioning") and captioner and captioner.enabled():
                    if frame_count % max(20, int(self.settings.emit_fps)) == 0:
                        try:
                            send_caption = captioner.generate(frame)
                        except Exception:
                            send_caption = None

                now = time.time()
                if now - last_emit >= 1.0 / max(1, self.settings.emit_fps):
                    last_emit = now
                    ok, buffer = cv2.imencode(".jpg", frame)
                    if not ok:
                        continue
                    jpg_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
                    socketio.emit(f"frame_{source}", {"image": jpg_b64})
                    if send_caption:
                        socketio.emit(f"caption_{source}", {"text": send_caption})
                    if send_counts:
                        socketio.emit(f"counts_{source}", send_counts)
                    if send_detections:
                        socketio.emit(f"detections_{source}", {"items": send_detections})

                time.sleep(0.001)
        finally:
            close_camera(cap)
