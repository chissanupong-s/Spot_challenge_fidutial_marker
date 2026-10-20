"""Live ArUco detection test on the Tello camera. The drone never takes off.

Run from the project root:
    python -m scripts.tello.marker_test --camera down
"""
from __future__ import annotations

import argparse
from pathlib import Path
import time
import cv2
import cv2.aruco as aruco

from scripts.aruco.calibration import calibration_mismatch, calibration_paths, load_calibration
from scripts.aruco.detector import ARUCO_DICTIONARIES, ArucoDistanceDetector
from scripts.aruco.utils import draw_frame_center, draw_text_block, ensure_dir, timestamp_filename
from scripts.tello.controller import TelloController


def parse_args():
    parser = argparse.ArgumentParser(description='Test ArUco detection on the Tello camera (no flying).')
    parser.add_argument('--camera', choices=['forward', 'down'], default='down')
    parser.add_argument('--marker-length', type=float, default=0.1825, help='Whole marker side in meters (for distance)')
    parser.add_argument('--dictionary', default='DICT_6X6_250', choices=sorted(ARUCO_DICTIONARIES.keys()))
    parser.add_argument('--ids', type=int, nargs='*', default=None, help='Only accept these IDs (default: any)')
    parser.add_argument('--display-scale', type=float, default=None,
                        help='Window zoom (default: 2 for down camera, 1 for forward)')
    return parser.parse_args()


def calibration_name(camera: str) -> str:
    return 'tello_down' if camera == 'down' else 'tello'


def try_load_calibration(camera: str):
    matrix_path, dist_path = calibration_paths(calibration_name(camera))
    if not (matrix_path.exists() and dist_path.exists()):
        print(f'No calibration in {matrix_path.parent} - detection only, no distances.')
        return None, None
    print(f'Loaded calibration from {matrix_path.parent}')
    return load_calibration(matrix_path, dist_path)


def marker_line(result) -> str:
    text = f"ID:{result['id']} area:{result['area_px']:.0f}px"
    if 'tz' in result:
        text += f" tx:{result['tx']:+.3f}m ty:{result['ty']:+.3f}m z:{result['tz']:.3f}m"
    return text


def main():
    args = parse_args()
    detector = ArucoDistanceDetector(
        marker_length=args.marker_length,
        dictionary=ARUCO_DICTIONARIES[args.dictionary],
        allowed_ids=args.ids,
    )

    controller = TelloController()
    battery = controller.connect()
    print(f'Tello battery: {battery}%')
    controller.start_video()

    camera = args.camera
    controller.set_downward_camera(camera == 'down')
    camera_matrix, dist_coeffs = try_load_calibration(camera)
    calibration_checked = False
    snapshot_dir = Path('data/snapshots')

    last_time = time.time()
    fps = 0.0
    print('Keys: v = switch camera, s = save snapshot, q = quit')

    try:
        while True:
            frame = controller.get_frame()
            if frame is None:
                cv2.waitKey(10)  # stream not decoded yet
                continue

            if camera_matrix is not None and not calibration_checked:
                warning = calibration_mismatch(camera_matrix, frame.shape)
                if warning:
                    print(f'WARNING: {warning}')
                calibration_checked = True

            raw = frame.copy()
            results, corners, ids = detector.detect(frame, camera_matrix, dist_coeffs)
            if ids is not None and len(corners) > 0:
                aruco.drawDetectedMarkers(frame, corners, ids)
                if camera_matrix is not None:
                    for result in results:
                        cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs,
                                          result['rvec'], result['tvec'], args.marker_length * 0.5)
            draw_frame_center(frame)

            now = time.time()
            fps = 0.9 * fps + 0.1 / max(now - last_time, 1e-6)
            last_time = now

            # Zoom only the displayed image; detection runs on the native frame
            scale = args.display_scale or (2.0 if camera == 'down' else 1.0)
            display = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST) if scale != 1.0 else frame

            h, w = raw.shape[:2]
            lines = [
                f'Camera: {camera} {w}x{h}  FPS: {fps:.1f}',
                f'Calibration: {"yes" if camera_matrix is not None else "NO (detection only)"}',
                f'Markers: {len(results)}',
            ] + [marker_line(r) for r in results[:5]]
            draw_text_block(display, lines, line_gap=26)
            cv2.imshow('Tello Marker Test', display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord('s'):
                ensure_dir(snapshot_dir)
                path = snapshot_dir / timestamp_filename(prefix=f'tello_{camera}', suffix='.jpg')
                cv2.imwrite(str(path), raw)
                print(f'Saved: {path}')
            elif key == ord('v'):
                try:
                    controller.set_downward_camera(camera != 'down')
                    camera = 'forward' if camera == 'down' else 'down'
                    camera_matrix, dist_coeffs = try_load_calibration(camera)
                    calibration_checked = False
                except RuntimeError as exc:
                    print(exc)
    finally:
        try:
            controller.set_downward_camera(False)
        except Exception:
            pass
        controller.end()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
