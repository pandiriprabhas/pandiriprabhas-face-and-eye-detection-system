import cv2
import time
import numpy as np

class FPSCounter:
    def __init__(self):
        self.last = time.time()
        self.fps = 0.0
        self.frames = 0

    def update(self):
        self.frames += 1
        now = time.time()
        dt = now - self.last
        if dt >= 1.0:
            self.fps = self.frames / dt
            self.frames = 0
            self.last = now
        return self.fps

def enhance_gray(gray):
    # Adaptive histogram equalization for better contrast under varied lighting
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)

def draw_detections(frame, faces, eyes):
    for det in faces:
        x,y,w,h = det.box
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
    for det in eyes:
        x,y,w,h = det.box
        cv2.rectangle(frame, (x,y), (x+w, y+h), (255,0,0), 1)
    return frame
