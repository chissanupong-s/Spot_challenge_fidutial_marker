"""Find which camera ID (0, 1, 2, ...) is which camera.

Run from the project root:
    python -m scripts.aruco.check_cameras
"""
from __future__ import annotations

import argparse
import cv2

from scripts.aruco.utils import draw_text_block


def parse_args():
    parser = argparse.ArgumentParser(description='Show every connected camera with its ID.')
    parser.add_argument('--max-id', type=int, default=4, help='Highest camera ID to try')
    return parser.parse_args()


def find_cameras(max_id: int) -> list[int]:
    found = []
    for camera_id in range(max_id + 1):
        cap = cv2.VideoCapture(camera_id)
        ok = cap.isOpened() and cap.read()[0]
        cap.release()
        if ok:
            found.append(camera_id)
    return found


def main():
    args = parse_args()
    print('Looking for cameras...')
    cameras = find_cameras(args.max_id)
    if not cameras:
        print('No camera found. Check that the webcam is plugged in and not used by another app.')
        return
    print(f'Found camera IDs: {cameras}')
    print('Keys: N = next camera, Q = quit')

    index = 0
    cap = cv2.VideoCapture(cameras[index])
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                frame = None
            if frame is not None:
                h, w = frame.shape[:2]
                draw_text_block(frame, [
                    f'CAMERA ID = {cameras[index]}',
                    f'Size: {w}x{h}',
                    'N = next camera, Q = quit',
                ], line_gap=34)
                cv2.imshow('Camera check', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord('n'):
                cap.release()
                index = (index + 1) % len(cameras)
                cap = cv2.VideoCapture(cameras[index])
                print(f'Showing camera ID {cameras[index]}')
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
