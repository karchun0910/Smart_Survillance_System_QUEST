import cv2
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


def check_camera(source: int) -> bool:
    camera = cv2.VideoCapture(source)

    try:
        if not camera.isOpened():
            return False

        frame_captured, _ = camera.read()
        return frame_captured
    finally:
        camera.release()


@router.get("/cameras/status")
def camera_status() -> dict[str, object]:
    source = int(get_settings().camera_source)

    return {
        "source": source,
        "available": check_camera(source),
    }
