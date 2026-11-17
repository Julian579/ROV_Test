import os
import time
from datetime import datetime
import cv2
import numpy as np
from flask import Flask, Response, jsonify, request


def make_app(cameras, vision, comms, timer):
    here = os.path.dirname(os.path.abspath(__file__))
    snap_dir = os.path.join(here, "snapshots")
    app = Flask(__name__, static_folder=os.path.join(here, "web"), static_url_path="")
    selected = {"index": 0, "dual": False}      # which camera / layout the page shows

    def no_signal(name):
        """Placeholder picture when a camera is unplugged or frozen."""
        img = np.full((480, 640, 3), (32, 38, 27), np.uint8)        # dark kelp (BGR)
        text, font = f"No signal: {name}", cv2.FONT_HERSHEY_SIMPLEX
        (w, h), _ = cv2.getTextSize(text, font, 0.9, 2)
        cv2.putText(img, text, ((640 - w) // 2, (480 + h) // 2), font, 0.9, (190, 200, 190), 2)
        return img

    def tile(cam, resize):
        frame = cam.get_frame() if cam.is_live() else None
        if frame is None:
            return no_signal(cam.name)
        frame = vision.update(frame)
        return cv2.resize(frame, (640, 480)) if resize else frame

    def displayed():
        """Cameras currently shown on the page."""
        return list(cameras) if selected["dual"] else [cameras[selected["index"]]]

    def render_view():
        """The exact picture the pilot sees (one camera, or both side by side)."""
        if selected["dual"]:
            return np.hstack([tile(c, True) for c in cameras])
        return tile(cameras[selected["index"]], False)

    def frames():
        """MJPEG stream: the browser keeps one <img> open and we keep pushing JPEGs."""
        while True:
            ok, jpg = cv2.imencode(".jpg", render_view(), [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
            time.sleep(0.03)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/video")
    def video():
        return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.get("/api/snapshot")
    def snapshot():
        if not any(c.is_live() for c in displayed()):
            return jsonify(ok=False, error="No live camera to save"), 409
        ok, jpg = cv2.imencode(".jpg", render_view(), [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ok:
            return jsonify(ok=False, error="Encoding failed"), 500
        name = datetime.now().strftime("rov_%Y%m%d_%H%M%S.jpg")
        os.makedirs(snap_dir, exist_ok=True)
        with open(os.path.join(snap_dir, name), "wb") as f:      # copy kept on the topside PC
            f.write(jpg.tobytes())
        return Response(jpg.tobytes(), mimetype="image/jpeg",
                        headers={"Content-Disposition": f'attachment; filename="{name}"',
                                 "X-Filename": name,
                                 "Access-Control-Expose-Headers": "X-Filename"})

    @app.get("/api/state")
    def state():
        t = comms.telemetry
        return jsonify(
            camera=selected["index"],
            dual=selected["dual"],
            cameras=[{"name": c.name, "live": c.is_live()} for c in cameras],
            filter=vision.enabled,
            link=(time.time() - comms.last_rx) < 1.0,
            roll=t["roll"], pitch=t["pitch"], yaw=t["yaw"],
            timer=timer.snapshot(),
        )

    @app.post("/api/camera")
    def set_camera():
        i = int(request.get_json()["index"])
        if 0 <= i < len(cameras):
            selected["index"] = i
        return jsonify(ok=True)

    @app.post("/api/view")
    def set_view():
        selected["dual"] = bool(request.get_json()["dual"])
        return jsonify(ok=True)

    @app.post("/api/filter")
    def set_filter():
        vision.enabled = bool(request.get_json()["on"])
        return jsonify(ok=True)

    @app.post("/api/timer/<action>")
    def timer_action(action):
        if action == "start":
            timer.start()
        elif action == "pause":
            timer.pause()
        elif action == "reset":
            timer.reset()
        return jsonify(ok=True)

    return app