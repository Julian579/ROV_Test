import struct

CMD_HEADER = 0xAA
TEL_HEADER = 0xBB

# header, surge, sway, heave, roll, pitch, yaw (floats), gripper (int8), checksum
CMD_FMT = "<B6fb"
TEL_FMT = "<B3f"   # header, roll, pitch, yaw (deg)


def _checksum(data: bytes) -> int:
    c = 0
    for b in data:
        c ^= b
    return c


def pack_command(surge, sway, heave, roll, pitch, yaw, gripper) -> bytes:
    body = struct.pack(CMD_FMT, CMD_HEADER, surge, sway, heave,
                       roll, pitch, yaw, int(gripper))
    return body + bytes([_checksum(body)])


def unpack_command(data: bytes):
    size = struct.calcsize(CMD_FMT)
    if len(data) != size + 1:
        return None
    if _checksum(data[:size]) != data[size]:
        return None
    h, surge, sway, heave, roll, pitch, yaw, grip = struct.unpack(CMD_FMT, data[:size])
    if h != CMD_HEADER:
        return None
    return {"cmd6": [surge, sway, heave, roll, pitch, yaw], "gripper": grip}


def pack_telemetry(roll, pitch, yaw) -> bytes:
    body = struct.pack(TEL_FMT, TEL_HEADER, roll, pitch, yaw)
    return body + bytes([_checksum(body)])


def unpack_telemetry(data: bytes):
    size = struct.calcsize(TEL_FMT)
    if len(data) != size + 1:
        return None
    if _checksum(data[:size]) != data[size]:
        return None
    h, roll, pitch, yaw = struct.unpack(TEL_FMT, data[:size])
    if h != TEL_HEADER:
        return None
    return {"roll": roll, "pitch": pitch, "yaw": yaw}
