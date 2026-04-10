import cv2


def open_camera(source: str):
    if source == "0":
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        return None
    return cap


def read_frame(cap):
    if cap is None:
        return None
    ok, frame = cap.read()
    return frame if ok else None


def close_camera(cap) -> None:
    if cap is not None:
        cap.release()
