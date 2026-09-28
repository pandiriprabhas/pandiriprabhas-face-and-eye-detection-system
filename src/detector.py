from __future__ import annotations
import cv2
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

@dataclass
class Detection:
    label: str
    box: Tuple[int, int, int, int]
    confidence: float | None = None

class HaarDetector:
    def __init__(self,
                 face_cascade: str = "haarcascade_frontalface_default.xml",
                 eye_cascade: str = "haarcascade_eye.xml",
                 scale_factor: float = 1.1,
                 min_neighbors: int = 5):
        base = Path(cv2.data.haarcascades)
        self.face_clf = cv2.CascadeClassifier(str(base / face_cascade))
        self.eye_clf = cv2.CascadeClassifier(str(base / eye_cascade))
        if self.face_clf.empty():
            raise FileNotFoundError("Failed to load face cascade")
        if self.eye_clf.empty():
            raise FileNotFoundError("Failed to load eye cascade")
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors

    def detect(self, frame_gray) -> Tuple[List[Detection], List[Detection]]:
        faces_rects = self.face_clf.detectMultiScale(frame_gray, self.scale_factor, self.min_neighbors)
        faces: List[Detection] = []
        eyes: List[Detection] = []
        for (x, y, w, h) in faces_rects:
            faces.append(Detection(label="face", box=(x, y, w, h)))
            roi_gray = frame_gray[y:y+h, x:x+w]
            eye_rects = self.eye_clf.detectMultiScale(roi_gray, 1.1, 3)
            # only keep eye detections in the upper half of the face rectangle to
            # avoid false positives on shirt/neck area when the camera isn't
            # perfectly focused on the eyes
            for (ex, ey, ew, eh) in eye_rects:
                # center y position of eye relative to face
                if ey + eh/2 > h/2:
                    continue
                eyes.append(Detection(label="eye", box=(x+ex, y+ey, ew, eh)))
        return faces, eyes
