import time
import config


class Timer:
    """Mission clock. Lives on the server so a page refresh never loses the time."""

    def __init__(self, total=config.TIMER_SECONDS):
        self.total = total
        self.paused_left = total     # seconds left while stopped
        self.end_at = None           # monotonic time when it reaches zero (only while running)

    def start(self):
        if self.end_at is None and self.paused_left > 0:
            self.end_at = time.monotonic() + self.paused_left

    def pause(self):
        if self.end_at is not None:
            self.paused_left = max(0.0, self.end_at - time.monotonic())
            self.end_at = None

    def reset(self):
        self.end_at = None
        self.paused_left = self.total

    def remaining(self):
        if self.end_at is None:
            return self.paused_left
        return max(0.0, self.end_at - time.monotonic())

    def snapshot(self):
        left = self.remaining()
        return {"remaining": left, "total": self.total,
                "running": self.end_at is not None and left > 0}