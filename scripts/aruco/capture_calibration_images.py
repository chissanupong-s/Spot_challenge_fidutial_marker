from __future__ import annotations

import argparse
from pathlib import Path
import cv2

from scripts.aruco.calibration import NATIVE_FRAME_SIZE
from scripts.aruco.utils import ensure_dir, timestamp_filename, draw_text_block


def parse_args():
    parser = argparse.ArgumentParser(description='Capture chessboard images for camera calibration.')
    parser.add_argument('--camera', choices=['webcam', 'tello', 'tello_down'], default='webcam',
                        help='Which camera to calibrate. Tello needs its Wi-Fi connected (it does not take off).')
    parser.add_argument('--camera-id', type=int, default=0, help='Webcam index, usually 0 (webcam only)')
    parser.add_argument('--output-dir', default=None, help='Default: data/calib_images/<camera>')
    parser.add_argument('--width', type=int, default=None, help='Requested capture width (webcam only)')
    parser.add_argument('--height', type=int, default=None, help='Requested capture height (webcam only)')
    parser.add_argument('--pattern-cols', type=int, default=9, help='Number of inner corners across columns')
    parser.add_argument('--pattern-rows', type=int, default=6, help='Number of inner corners across rows')
    return parser.parse_args()


def board_visible(frame, pattern_size, max_width=640) -> bool:
    """Fast check that the whole chessboard is in view (on a downscaled copy, to keep the preview smooth)."""
    scale = min(1.0, max_width / frame.shape[1])
    small = cv2.resize(frame, None, fx=scale, fy=scale) if scale < 1.0 else frame
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
    found, _ = cv2.findChessboardCorners(gray, pattern_size, flags)
    return found


class WebcamSource:
    def __init__(self, camera_id: int, width: int, height: int):
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError(f'Could not open camera {camera_id}')

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError('Failed to read webcam frame')
        return frame

    def close(self):
        self.cap.release()


class TelloSource:
    def __init__(self, downward: bool = False):
        from scripts.tello.controller import TelloController
        self.controller = TelloController()
        battery = self.controller.connect()
        print(f'Tello battery: {battery}%')
        self.controller.start_video()
        if downward:
            self.controller.set_downward_camera(True)

    def read(self):
        return self.controller.get_frame()

    def close(self):
        self.controller.end()


def main():
    args = parse_args()
    output_dir = ensure_dir(args.output_dir or f'data/calib_images/{args.camera}')

    if args.camera in ('tello', 'tello_down'):
        source = TelloSource(downward=args.camera == 'tello_down')
    else:
        default_w, default_h = NATIVE_FRAME_SIZE['webcam']
        source = WebcamSource(args.camera_id, args.width or default_w, args.height or default_h)

    saved_count = len(list(Path(output_dir).glob('*.jpg')))

    try:
        while True:
            frame = source.read()
            if frame is None:
                cv2.waitKey(1)
                continue

            h, w = frame.shape[:2]
            found = board_visible(frame, (args.pattern_cols, args.pattern_rows))
            overlay = frame.copy()
            draw_text_block(overlay, [
                f'Calibration capture ({args.camera} {w}x{h})',
                'BOARD FOUND - press SPACE to save' if found else 'Board not found - show the WHOLE board',
                'Press Q to quit',
                f'Saved: {saved_count}',
            ], color=(0, 255, 0) if found else (0, 0, 255))
            cv2.imshow('Capture Calibration Images', overlay)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') and not found:
                print('Not saved: the whole chessboard must be visible.')
            elif key == ord(' '):
                filename = output_dir / timestamp_filename(prefix='calib', suffix='.jpg')
                cv2.imwrite(str(filename), frame)
                saved_count += 1
                print(f'Saved: {filename}')
            elif key == ord('q'):
                break
    finally:
        source.close()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
