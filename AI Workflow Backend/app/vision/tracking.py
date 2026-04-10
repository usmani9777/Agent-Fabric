from collections import Counter

import cv2


def track_objects(model, frame, conf_threshold: float = 0.5, counting: bool = False):
    results = model.track(source=frame, persist=True, conf=conf_threshold, verbose=False)[0]

    bboxes = []
    class_ids = []
    track_ids = []
    scores = []
    class_names = model.names

    for box in results.boxes:
        if box.id is None:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        track_id = int(box.id[0])
        bboxes.append([int(x1), int(y1), int(x2), int(y2)])
        class_ids.append(cls)
        track_ids.append(track_id)
        scores.append(conf)

    if counting:
        counts = Counter([class_names[cid] for cid in class_ids])
        return bboxes, class_ids, track_ids, scores, frame, class_names, dict(counts)

    return bboxes, class_ids, track_ids, scores, frame, class_names


def draw_tracks(frame, bboxes, class_ids, track_ids, scores, class_names):
    for bbox, cls, tid, score in zip(bboxes, class_ids, track_ids, scores):
        x1, y1, x2, y2 = bbox
        color = (tid * 50 % 255, tid * 80 % 255, tid * 120 % 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"ID {tid} | {class_names[cls]} {score:.2f}"
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - text_h - 10), (x1 + text_w, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    return frame
