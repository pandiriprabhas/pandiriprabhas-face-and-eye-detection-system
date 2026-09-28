import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk

from .detector import HaarDetector
from .utils import FPSCounter, enhance_gray, draw_detections
from .video import open_source

class CaptureGUI:
    def __init__(self, root: tk.Tk, source, backend: str | None = None,
                 scale_factor: float = 1.1, min_neighbors: int = 5, width: int = 0,
                 save_dir: Path = Path("data/captures")):
        self.root = root
        self.root.title("Enhanced Face & Eye Detection - GUI")
        self.source = source
        self.backend = backend
        self.width = width
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # Video
        self.cap = open_source(source, backend)
        # Detection
        self.detector = HaarDetector(scale_factor=scale_factor, min_neighbors=min_neighbors)
        self.fpsc = FPSCounter()

        # UI
        self.video_label = tk.Label(root)
        self.video_label.pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, pady=8)

        self.capture_btn = tk.Button(btn_frame, text="Capture", command=self.capture_frame)
        self.capture_btn.pack(side=tk.LEFT, padx=5)

        self.quit_btn = tk.Button(btn_frame, text="Quit", command=self.quit)
        self.quit_btn.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(root, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        # allow space bar to capture frame
        self.root.bind("<space>", lambda e: self.capture_frame())
        self.current_frame = None
        self._update_frame()

    def _update_frame(self):
        ok, frame = self.cap.read()
        if not ok:
            self.status_var.set("End of stream / read failure")
            self.root.after(200, self._update_frame)
            return
        if self.width > 0:
            frame = cv2.resize(frame, (self.width, int(frame.shape[0]*self.width/frame.shape[1])))
        gray = enhance_gray(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        faces, eyes = self.detector.detect(gray)
        annotated = draw_detections(frame.copy(), faces, eyes)
        fps = self.fpsc.update()
        cv2.putText(annotated, f"Faces: {len(faces)} Eyes: {len(eyes)} FPS: {fps:.1f}", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

        # Convert to Tk image
        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk  # keep reference
        self.video_label.configure(image=imgtk)

        self.current_frame = annotated
        self.root.after(10, self._update_frame)

    def capture_frame(self):
        if self.current_frame is None:
            return
        filename = self.save_dir / f"capture_{cv2.getTickCount()}.png"
        cv2.imwrite(str(filename), self.current_frame)
        self.status_var.set(f"Saved: {filename}")

    def quit(self):
        try:
            if self.cap:
                self.cap.release()
        finally:
            self.root.destroy()


def launch_gui(source: str = "0", backend: str = "auto", scale_factor: float = 1.1,
               min_neighbors: int = 5, width: int = 0):
        root = tk.Tk()
        app = CaptureGUI(root, source, backend, scale_factor, min_neighbors, width)
        root.mainloop()
