import cv2
import sys
from pathlib import Path

__all__ = ["open_source"]

def _backend_from_name(name: str | None):
    if not name or name.lower() == "auto":
        return None
    name = name.lower()
    mapping = {
        "avfoundation": getattr(cv2, "CAP_AVFOUNDATION", 0),
        "qt": getattr(cv2, "CAP_QT", 1),
        "any": getattr(cv2, "CAP_ANY", 0),
        "v4l2": getattr(cv2, "CAP_V4L2", 200),
    }
    return mapping.get(name, None)


def open_source(source: str | int, backend: str | None = None):
    be_flag = _backend_from_name(backend)
    def _try_open(src, flag=None):
        return cv2.VideoCapture(src, flag) if flag is not None else cv2.VideoCapture(src)

    cap = None
    is_index = False
    if isinstance(source, int):
        is_index = True
    else:
        if str(source).isdigit() and Path(source).exists() is False:
            source = int(source)
            is_index = True
        else:
            # If a non-index was provided, ensure the file exists before opening
            p = Path(str(source))
            if not p.exists():
                raise RuntimeError(f"File not found: {p}")

    tried = []
    if be_flag is not None:
        cap = _try_open(source, be_flag); tried.append((source, be_flag))
    elif sys.platform == "darwin" and is_index:
        cap = _try_open(source, getattr(cv2, "CAP_AVFOUNDATION", 0)); tried.append((source, getattr(cv2, "CAP_AVFOUNDATION", 0)))
        if not cap.isOpened():
            cap.release()
            cap = _try_open(source); tried.append((source, None))
    else:
        cap = _try_open(source); tried.append((source, None))

    if not cap or not cap.isOpened():
        hint = ""
        if sys.platform == "darwin" and is_index:
            hint = (
                "On macOS, grant Camera permission to the app running Python (e.g., Visual Studio Code or Terminal) under Settings > Privacy & Security > Camera. "
                "Then fully quit and reopen it. You can also try --backend avfoundation."
            )
        raise RuntimeError(f"Cannot open video source: {source}. {hint}")
    return cap
