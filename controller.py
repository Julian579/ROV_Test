import pygame
from pygame._sdl2 import controller as sdl
import config


class Controller:
    def __init__(self):
        pygame.init()
        sdl.init()
        self.pad = None
        self._connect()          # raises a clear error if no pad at startup

    def _connect(self):
        # Find the first gamepad that SDL recognizes
        for i in range(sdl.get_count()):
            if sdl.is_controller(i):
                self.pad = sdl.Controller(i)
                print("Gamepad connected:", self.pad.name)
                return
        self.pad = None
        raise RuntimeError("No supported gamepad found")

    def _axis(self, axis_id):
        """Raw SDL axis is -32768..32767; return -1..1 with deadzone."""
        v = self.pad.get_axis(axis_id) / 32767.0
        v = max(-1.0, min(1.0, v))
        return 0.0 if abs(v) < config.DEADZONE else v

    def update(self):
        """Returns (surge, sway, heave, roll, pitch, yaw, gripper)."""
        pygame.event.pump()

        # Safety: if the pad is unplugged, command zero and try to reconnect
        if self.pad is None or not self.pad.attached():
            try:
                self._connect()
            except RuntimeError:
                return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0

        # SDL convention: stick pushed UP gives a NEGATIVE Y value, so we invert it
        surge = -self._axis(pygame.CONTROLLER_AXIS_LEFTY)    # left stick up = forward
        sway  =  self._axis(pygame.CONTROLLER_AXIS_LEFTX)    # left stick right
        yaw   =  self._axis(pygame.CONTROLLER_AXIS_RIGHTX)   # right stick right
        heave = -self._axis(pygame.CONTROLLER_AXIS_RIGHTY)   # right stick up = ascend

        gripper = 0
        if self.pad.get_button(pygame.CONTROLLER_BUTTON_LEFTSHOULDER):      # L1 = open
            gripper = -1
        elif self.pad.get_button(pygame.CONTROLLER_BUTTON_RIGHTSHOULDER):   # R1 = close
            gripper = 1

        # roll/pitch come from the MCU PID, so the operator sends 0
        return surge, sway, heave, 0.0, 0.0, yaw, gripper