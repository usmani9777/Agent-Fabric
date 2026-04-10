from PIL import Image

try:
    from cloud_based_Captioning import FrameCaptioner  # type: ignore
except Exception:  # pragma: no cover
    FrameCaptioner = None


class CaptionService:
    def __init__(self) -> None:
        self._captioner = FrameCaptioner() if FrameCaptioner else None

    def enabled(self) -> bool:
        return self._captioner is not None

    def generate(self, frame):
        if self._captioner is None:
            return None
        pil_image = Image.fromarray(frame)
        return self._captioner.generate_caption(pil_image)
