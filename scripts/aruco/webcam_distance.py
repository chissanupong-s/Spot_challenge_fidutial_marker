from __future__ import annotations

import argparse
import cv2
import cv2.aruco as aruco

from scripts.aruco.calibration import calibration_mismatch, calibration_paths, load_calibration
from scripts.aruco.detector import ArucoDistanceDetector
from scripts.aruco.utils import draw_info


def parse_args():
    parser = argparse.ArgumentParser(description='ArUco distance detector (webcam only)')
    parser.add_argument('--marker-length', type=float, default=0.1825, help='Real marker side length in meters')
    parser.add_argument('--camera-id', type=int, default=0, help='Webcam index')
    parser.add_argument('--camera-matrix', type=str, default=str(calibration_paths('webcam')[0]))
    parser.add_argument('--dist-coeffs', type=str, default=str(calibration_paths('webcam')[1]))
    parser.add_argument('--width', type=int, default=1280)
    parser.add_argument('--height', type=int, default=720)
    return parser.parse_args()


def main():
    args = parse_args()
    camera_matrix, dist_coeffs = load_calibration(args.camera_matrix, args.dist_coeffs)
    detector = ArucoDistanceDetector(
        marker_length=args.marker_length,
        dictionary=aruco.DICT_6X6_250,
        allowed_ids={0, 1, 2, 3, 4},
    )

    cap = cv2.VideoCapture(args.camera_id)
    if args.width > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height > 0:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not cap.isOpened():
        raise RuntimeError(f'Could not open camera with index {args.camera_id}')

    print('Press Q to quit.')
    calibration_checked = False
    while True:
        ret, frame = cap.read()
        if not ret:
            print('Failed to read frame from camera.')
            break
        if not calibration_checked:
            warning = calibration_mismatch(camera_matrix, frame.shape)
            if warning:
                print(f'WARNING: {warning}')
            calibration_checked = True

        results, corners, ids = detector.detect(frame, camera_matrix, dist_coeffs)
        if ids is not None and len(corners) > 0:
            aruco.drawDetectedMarkers(frame, corners, ids)
            for i, result in enumerate(results):
                cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, result['rvec'], result['tvec'], args.marker_length * 0.5)
                draw_info(frame, result, y=40 + i * 35)

        cv2.putText(frame, 'Allowed IDs: 0, 1, 2, 3, 4 | Press Q to quit', (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.imshow('ArUco Distance Detector', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
