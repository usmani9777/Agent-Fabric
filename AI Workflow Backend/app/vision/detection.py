import cv2
import torch
from ultralytics import YOLO


def load_yolo_model(model_path: str):
    model = YOLO(model_path, verbose=False)
    if torch.cuda.is_available():
        model.to("cuda")
    return model


def detect_objects(model, frame, conf_threshold: float = 0.5):
    results = model(frame)[0]

    bboxes: list[list[int]] = []
    class_ids: list[int] = []
    scores: list[float] = []
    class_names = model.names

    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        if conf >= conf_threshold:
            bboxes.append([int(x1), int(y1), int(x2), int(y2)])
            class_ids.append(cls)
            scores.append(conf)

    return bboxes, class_ids, scores, frame, class_names


def draw_detections(frame, bboxes, class_ids, scores, class_names):
    for bbox, cls, score in zip(bboxes, class_ids, scores):
        x1, y1, x2, y2 = bbox
        color = (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{class_names[cls]} {score:.2f}"
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - text_h - 10), (x1 + text_w, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    return frame
