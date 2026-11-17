# Web will be Used instead of GUI, but keeping GUI for now in case we want to use it for testing
import tkinter as tk
import cv2
from PIL import Image, ImageTk


class Gui:
    def __init__(self, camera, vision, comms):
        self.camera, self.vision, self.comms = camera, vision, comms
        self.root = tk.Tk()
        self.root.title("ROV Topside")

        self.video = tk.Label(self.root)
        self.video.pack()

        self.tel = tk.Label(self.root, font=("Consolas", 12), text="")
        self.tel.pack()

        self.blue = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Blue filter", variable=self.blue,
                       command=self._toggle).pack()

        self._refresh()

    def _toggle(self):
        self.vision.enabled = self.blue.get()

    def _refresh(self):
        frame = self.camera.get_frame()
        if frame is not None:
            frame = self.vision.update(frame)
            frame = cv2.resize(frame, (640, 480))
            img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.video.configure(image=img)
            self.video.image = img
        t = self.comms.telemetry
        self.tel.configure(text=f"Roll {t['roll']:6.1f}  Pitch {t['pitch']:6.1f}  Yaw {t['yaw']:6.1f}")
        self.root.after(33, self._refresh)

    def run(self):
        self.root.mainloop()
