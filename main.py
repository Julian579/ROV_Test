import threading
import time
import config
from controller import Controller
from comms import Comms
from camera import Camera
from vision import Vision
from mission_timer import Timer
from server import make_app


def control_loop(controller, comms, stop):
    period = 1.0 / config.CONTROL_HZ
    while not stop.is_set():
        t0 = time.time()
        comms.send(*controller.update())
        time.sleep(max(0.0, period - (time.time() - t0)))


def main():
    controller = Controller()
    comms = Comms()
    cameras = [Camera(c["name"], c["source"]) for c in config.CAMERAS]
    vision = Vision()
    timer = Timer()
    stop = threading.Event()

    threading.Thread(target=control_loop, args=(controller, comms, stop), daemon=True).start()
    for cam in cameras:
        threading.Thread(target=cam.run, daemon=True).start()

    app = make_app(cameras, vision, comms, timer)
    print(f"Pilot page: http://localhost:{config.WEB_PORT}")
    try:
        app.run(host=config.WEB_HOST, port=config.WEB_PORT, threaded=True)
    finally:
        stop.set()
        for cam in cameras:
            cam.close()
        comms.close()


if __name__ == "__main__":
    main()