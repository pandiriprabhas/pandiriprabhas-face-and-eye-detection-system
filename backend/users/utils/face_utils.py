from __future__ import annotations
from pathlib import Path
import cv2

def detect_face_box(image_path: str | Path):
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
    faces = cascade.detectMultiScale(gray, 1.1, 5)
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
    return {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}

def detect_face_and_eyes(image_path: str | Path):
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    base = Path(cv2.data.haarcascades)
    face_cascade = cv2.CascadeClassifier(str(base / "haarcascade_frontalface_default.xml"))
    eye_cascade = cv2.CascadeClassifier(str(base / "haarcascade_eye.xml"))
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
    face_box = {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
    roi_gray = gray[y:y+h, x:x+w]
    eye_rects = eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
    filtered_eyes = []
    for ex, ey, ew, eh in eye_rects:
        if ey + eh / 2 > h / 2:
            continue
        filtered_eyes.append({"x": int(x+ex), "y": int(y+ey), "width": int(ew), "height": int(eh)})
    return {"face_box": face_box, "eyes": filtered_eyes, "eye_count": len(filtered_eyes)}

def extract_face_encoding(image_path: str | Path):
    try:
        import face_recognition
    except Exception:
        return None
    image = face_recognition.load_image_file(str(image_path))
    encodings = face_recognition.face_encodings(image)
    return encodings[0].tolist() if encodings else None
