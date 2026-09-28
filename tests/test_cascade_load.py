import cv2
from pathlib import Path
from src.detector import HaarDetector

def test_cascades_load():
    det = HaarDetector()
    # Simple assertions that cascades are initialized (OpenCV CascadeClassifier has empty() method)
    assert not det.face_clf.empty()
    assert not det.eye_clf.empty()


def test_space_capture(tmp_path, monkeypatch):
    """Running the CLI with a fake camera should save a snapshot on space bar."""
    import numpy as np
    from src.app import run as face_run
    # dummy capture that yields one black frame then stops
    class DummyCap:
        def __init__(self):
            self.calls = 0
        def read(self):
            if self.calls == 0:
                self.calls += 1
                # 100x100 black image
                return True, np.zeros((100, 100, 3), dtype=np.uint8)
            return False, None
        def release(self):
            pass
        def isOpened(self):
            return True
    monkeypatch.setattr('src.video.open_source', lambda src, backend=None: DummyCap())
    # intercept imwrite calls so we can verify path and make file
    written = []
    def fake_imwrite(path, img):
        written.append(path)
        # actually write something so file exists
        with open(path, 'wb') as f:
            f.write(b'x')
        return True
    monkeypatch.setattr('cv2.imwrite', fake_imwrite)
    # suppress imshow and putText
    monkeypatch.setattr('cv2.imshow', lambda *args, **kwargs: None)
    monkeypatch.setattr('cv2.putText', lambda *args, **kwargs: None)

    # simulate key presses: space then 'q'
    keys = [ord(' '), ord('q')]
    def fake_waitkey(delay):
        return keys.pop(0)
    monkeypatch.setattr('cv2.waitKey', fake_waitkey)

    # run with capture_dir pointing at tmp_path
    # supply concrete values for all parameters to avoid OptionInfo defaults
    face_run("0", False, Path("output.mp4"), 1.1, 5, 0, "auto", tmp_path)
    # verify snapshot was written
    assert len(written) == 1
    assert tmp_path in Path(written[0]).parents


def test_eye_filtering():
    """Eye detections below mid-face should be ignored."""
    import numpy as np
    from src.detector import HaarDetector, Detection
    # create detector and replace classifiers with simple fakes
    det = HaarDetector()
    class FakeFace:
        def detectMultiScale(self, img, sf, mn):
            return [(0,0,100,100)]
    class FakeEye:
        def detectMultiScale(self, img, sf, mn):
            # high eye and low eye
            return [(10,20,15,15),(10,60,15,15)]
    det.face_clf = FakeFace()
    det.eye_clf = FakeEye()
    faces, eyes = det.detect(np.zeros((100,100), dtype=np.uint8))
    assert len(faces) == 1
    # only the upper eye should survive
    assert len(eyes) == 1
    assert eyes[0].box[1] == 20
