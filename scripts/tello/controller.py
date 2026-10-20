from __future__ import annotations

from dataclasses import dataclass
import time

import cv2

try:
    from djitellopy import Tello
except Exception:  # pragma: no cover
    Tello = None


# Limits from the Tello SDK
MOVE_MIN_CM, MOVE_MAX_CM = 20, 500
ROTATE_MIN_DEG, ROTATE_MAX_DEG = 1, 360
RC_MIN, RC_MAX = -100, 100
# The Tello auto-lands after 15 s without any command
KEEPALIVE_INTERVAL_S = 5.0


def _clamp(value, low, high):
    return max(low, min(high, int(value)))


@dataclass
class TelloStatus:
    connected: bool = False
    battery: int | None = None
    in_air: bool = False


class TelloController:
    def __init__(self):
        if Tello is None:
            raise ImportError('djitellopy is not installed. Run: pip install djitellopy')
        self.tello = Tello()
        self.status = TelloStatus()
        self.last_command_time = 0.0

    @property
    def in_air(self) -> bool:
        return self.status.in_air

    def connect(self):
        self.tello.connect()
        self.status.connected = True
        try:
            self.status.battery = self.tello.get_battery()
        except Exception:
            self.status.battery = None
        return self.status.battery

    def start_video(self):
        try:
            self.tello.streamoff()
        except Exception:
            pass
        self.tello.streamon()
        time.sleep(1.0)

    def set_downward_camera(self, downward: bool):
        """Switch the video stream between the forward and downward camera.

        Uses the SDK 2.0 'downvision' command, which stock Ryze Tello firmware may reject.
        """
        direction = Tello.CAMERA_DOWNWARD if downward else Tello.CAMERA_FORWARD
        try:
            self.tello.set_video_direction(direction)
        except Exception as exc:
            raise RuntimeError(
                f'Tello rejected the camera switch ({exc}). The downward camera needs '
                'Tello EDU / Tello TT firmware (SDK 2.0+).'
            ) from exc

    def get_frame(self):
        """Return the latest frame as BGR, or None until the first real frame is decoded."""
        frame = self.tello.get_frame_read().frame
        # djitellopy starts with an all-black placeholder before the stream decodes
        if frame is None or not frame.any():
            return None
        if frame.ndim == 2:  # grayscale (downward camera)
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        # djitellopy decodes frames as RGB; OpenCV expects BGR
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def takeoff(self):
        self.tello.takeoff()
        self.status.in_air = True

    def land(self):
        self.tello.land()
        self.status.in_air = False

    def stop_motion(self):
        self.send_rc(0, 0, 0, 0)

    def keepalive(self):
        """Send a zero RC command if nothing was sent recently, so a hovering Tello doesn't auto-land.

        Uses rc instead of the 'keepalive' command, which stock (non-EDU) Tello firmware doesn't support.
        """
        if self.status.in_air and time.time() - self.last_command_time > KEEPALIVE_INTERVAL_S:
            self.stop_motion()

    def send_rc(self, lr: int, fb: int, ud: int, yaw: int):
        self.last_command_time = time.time()
        self.tello.send_rc_control(
            _clamp(lr, RC_MIN, RC_MAX),
            _clamp(fb, RC_MIN, RC_MAX),
            _clamp(ud, RC_MIN, RC_MAX),
            _clamp(yaw, RC_MIN, RC_MAX),
        )

    def move_left(self, cm=30):
        self.last_command_time = time.time()
        self.tello.move_left(_clamp(cm, MOVE_MIN_CM, MOVE_MAX_CM))

    def move_right(self, cm=30):
        self.last_command_time = time.time()
        self.tello.move_right(_clamp(cm, MOVE_MIN_CM, MOVE_MAX_CM))

    def move_forward(self, cm=30):
        self.last_command_time = time.time()
        self.tello.move_forward(_clamp(cm, MOVE_MIN_CM, MOVE_MAX_CM))

    def move_back(self, cm=30):
        self.last_command_time = time.time()
        self.tello.move_back(_clamp(cm, MOVE_MIN_CM, MOVE_MAX_CM))

    def move_up(self, cm=30):
        self.last_command_time = time.time()
        self.tello.move_up(_clamp(cm, MOVE_MIN_CM, MOVE_MAX_CM))

    def move_down(self, cm=20):
        self.last_command_time = time.time()
        self.tello.move_down(_clamp(cm, MOVE_MIN_CM, MOVE_MAX_CM))

    def rotate_clockwise(self, deg=20):
        self.last_command_time = time.time()
        self.tello.rotate_clockwise(_clamp(deg, ROTATE_MIN_DEG, ROTATE_MAX_DEG))

    def rotate_counter_clockwise(self, deg=20):
        self.last_command_time = time.time()
        self.tello.rotate_counter_clockwise(_clamp(deg, ROTATE_MIN_DEG, ROTATE_MAX_DEG))

    def end(self):
        try:
            self.tello.streamoff()
        except Exception:
            pass
        self.tello.end()
