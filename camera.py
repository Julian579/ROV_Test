import threading
import time
import cv2


class Camera:
    def __init__(self, name, source):
        self.name = name
        self.cap = cv2.VideoCapture(source)
        self.frame = None
        self.last_ok = 0.0               # time of the last good frame
        self.lock = threading.Lock()
        self.running = True

    def run(self):
        """Thread target: keep grabbing the latest frame."""
        while self.running:
            ok, f = self.cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            with self.lock:
                self.frame = f
                self.last_ok = time.time()

    def is_live(self):
        """True if a frame arrived in the last second."""
        return (time.time() - self.last_ok) < 1.0

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def close(self):
        self.running = False
        self.cap.release()