import numpy as np

# For studying on one PC use 127.0.0.1. For the real ROV change to its IP.
ROV_IP = "127.0.0.1"
ROV_PORT = 5005
TOPSIDE_PORT = 5006          # telemetry comes back here
CONTROL_HZ = 50

CAMERAS = [
    {"name": "Front", "source": "192.168.1.60"},
    {"name": "Down",  "source": "192.168.1.61"},
]
WEB_HOST = "127.0.0.1"   # "0.0.0.0" lets other laptops on the network open the page
WEB_PORT = 8000
TIMER_SECONDS = 15 * 60           # 0 = USB cam, or "rtsp://..." / "http://..."

DEADZONE = 0.08

# Blue filter (OpenCV HSV: H 0-179)
BLUE_LOW = np.array([90, 60, 40])
BLUE_HIGH = np.array([130, 255, 255])

# Thrusters: position (x fwd, y right, z down) in m, thrust direction unit vector
s = 2 ** -0.5
THRUSTERS = [
    {"pos": ( 0.20,  0.15, 0.0), "dir": ( s, -s, 0)},   # 0 front-right
    {"pos": ( 0.20, -0.15, 0.0), "dir": ( s,  s, 0)},   # 1 front-left
    {"pos": (-0.20,  0.15, 0.0), "dir": ( s,  s, 0)},   # 2 rear-right
    {"pos": (-0.20, -0.15, 0.0), "dir": ( s, -s, 0)},   # 3 rear-left
    {"pos": ( 0.00,  0.15, 0.0), "dir": ( 0,  0, 1)},   # 4 vertical-right
    {"pos": ( 0.00, -0.15, 0.0), "dir": ( 0,  0, 1)},   # 5 vertical-left
]
