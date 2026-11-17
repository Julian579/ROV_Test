import socket
import threading
import time
import config
import protocol


class Comms:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", config.TOPSIDE_PORT))
        self.sock.settimeout(0.5)
        self.last_rx = 0.0

        self.addr = (config.ROV_IP, config.ROV_PORT)
        self.telemetry = {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}
        self.running = True
        threading.Thread(target=self._rx_loop, daemon=True).start()

    def send(self, surge, sway, heave, roll, pitch, yaw, gripper):
        pkt = protocol.pack_command(surge, sway, heave, roll, pitch, yaw, gripper)
        self.sock.sendto(pkt, self.addr)

    def _rx_loop(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(64)
            except socket.timeout:
                continue
            except OSError:
                break
            t = protocol.unpack_telemetry(data)
            if t:
                self.telemetry = t
                self.last_rx = time.time()
        
    def close(self):
        self.running = False
        self.sock.close()
