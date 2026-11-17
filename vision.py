import cv2
import config


class Vision:
    def __init__(self):
        self.enabled = False

    def update(self, frame):
        """Frame in, frame out. Keeps only blue shades when enabled."""
        if not self.enabled:
            return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, config.BLUE_LOW, config.BLUE_HIGH)
        return cv2.bitwise_and(frame, frame, mask=mask)
