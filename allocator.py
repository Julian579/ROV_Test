class Allocator:
    """Mixes a 6-DOF command into one value per thruster."""

    def __init__(self):
        # per-axis gains for tuning: surge, sway, heave, roll, pitch, yaw
        self.gains = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    def update(self, cmd6):
        """cmd6 = [surge, sway, heave, roll, pitch, yaw] -> 6 values in [-1, 1]."""
        surge, sway, heave, roll, pitch, yaw = [c * g for c, g in zip(cmd6, self.gains)]

        u = [
            surge - sway - yaw,   # 0 front-right
            surge + sway + yaw,   # 1 front-left
            surge + sway - yaw,   # 2 rear-right
            surge - sway + yaw,   # 3 rear-left
            heave + roll,         # 4 vertical-right
            heave - roll,         # 5 vertical-left
        ]                          # pitch is unused: this layout can't produce it

        # if any thruster is over 100%, scale all of them down together
        m = max(abs(v) for v in u)
        if m > 1.0:
            u = [v / m for v in u]
        return u


if __name__ == "__main__":
    a = Allocator()
    print("surge:", a.update([1, 0, 0, 0, 0, 0]))
    print("sway :", a.update([0, 1, 0, 0, 0, 0]))
    print("heave:", a.update([0, 0, 1, 0, 0, 0]))
    print("yaw  :", a.update([0, 0, 0, 0, 0, 1]))
    print("mixed:", a.update([1, 0, 0, 0, 0, 1]))