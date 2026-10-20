from __future__ import annotations

import argparse
from pathlib import Path
import glob
import cv2
import numpy as np

from scripts.aruco.calibration import CALIBRATION_ROOT, calibration_paths, save_calibration
from scripts.aruco.utils import ensure_dir


def mean_reprojection_error(objpoints, imgpoints, rvecs, tvecs, camera_matrix, dist_coeffs) -> float:
    total_error = 0.0
    total_points = 0
    for objp, imgp, rvec, tvec in zip(objpoints, imgpoints, rvecs, tvecs):
        projected, _ = cv2.projectPoints(objp, rvec, tvec, camera_matrix, dist_coeffs)
        error = cv2.norm(imgp, projected, cv2.NORM_L2)
        total_error += error ** 2
        total_points += len(objp)
    if total_points == 0:
        return float('inf')
    return float(np.sqrt(total_error / total_points))


def parse_args():
    parser = argparse.ArgumentParser(description='Calibrate a camera from checkerboard images.')
    parser.add_argument('--camera', choices=['webcam', 'tello', 'tello_down'], default='webcam',
                        help='Which camera the images came from; picks the default input/output paths')
    parser.add_argument('--images', default=None, help='Glob pattern for calibration images. Default: data/calib_images/<camera>/*.jpg')
    parser.add_argument('--pattern-cols', type=int, default=9, help='Number of inner corners across columns')
    parser.add_argument('--pattern-rows', type=int, default=6, help='Number of inner corners across rows')
    parser.add_argument('--square-size', type=float, default=0.021, help='Checkerboard square size in meters')
    parser.add_argument('--camera-matrix-out', default=None, help='Default: assets/calibration/<camera>/camera_matrix.npy')
    parser.add_argument('--dist-coeffs-out', default=None, help='Default: assets/calibration/<camera>/dist_coeffs.npy')
    parser.add_argument('--report-out', default=None, help='Default: assets/calibration/<camera>/reprojection_report.txt')
    args = parser.parse_args()

    default_matrix, default_dist = calibration_paths(args.camera)
    args.images = args.images or f'data/calib_images/{args.camera}/*.jpg'
    args.camera_matrix_out = args.camera_matrix_out or str(default_matrix)
    args.dist_coeffs_out = args.dist_coeffs_out or str(default_dist)
    args.report_out = args.report_out or str(CALIBRATION_ROOT / args.camera / 'reprojection_report.txt')
    return args


def main():
    args = parse_args()
    pattern_size = (args.pattern_cols, args.pattern_rows)

    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001,
    )

    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    objp *= args.square_size

    objpoints = []
    imgpoints = []
    images = sorted(glob.glob(args.images))

    if not images:
        raise FileNotFoundError(f'No images matched: {args.images}')

    image_size = None
    good_images = 0
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE

    for filename in images:
        image = cv2.imread(filename)
        if image is None:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if image_size is not None and gray.shape[::-1] != image_size:
            print(f'Skipped (size {gray.shape[::-1]} differs from {image_size}): {filename}')
            continue
        image_size = gray.shape[::-1]

        if hasattr(cv2, 'findChessboardCornersSB'):
            found, corners = cv2.findChessboardCornersSB(gray, pattern_size)
        else:
            found, corners = cv2.findChessboardCorners(gray, pattern_size, flags)
        if not found:
            print(f'Skipped (corners not found): {filename}')
            continue

        refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria) if corners is not None else corners
        objpoints.append(objp)
        imgpoints.append(refined if refined is not None else corners)
        good_images += 1
        print(f'Accepted: {filename}')

    if good_images < 10:
        raise RuntimeError(f'Only {good_images} valid calibration images found. Use at least 10 clear views.')

    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints,
        imgpoints,
        image_size,
        None,
        None,
    )

    mean_error = mean_reprojection_error(objpoints, imgpoints, rvecs, tvecs, camera_matrix, dist_coeffs)
    ensure_dir(Path(args.camera_matrix_out).parent)
    save_calibration(camera_matrix, dist_coeffs, args.camera_matrix_out, args.dist_coeffs_out)

    report = (
        f'RMS returned by calibrateCamera: {rms}\n'
        f'Mean reprojection error (pixels): {mean_error}\n'
        f'Camera: {args.camera}\n'
        f'Image size (w, h): {image_size}\n'
        f'Valid calibration images: {good_images}\n'
        f'Pattern size (inner corners): {pattern_size}\n'
        f'Square size (meters): {args.square_size}\n'
    )
    Path(args.report_out).write_text(report, encoding='utf-8')

    print('\nCalibration complete.')
    print(report)
    print('Camera matrix:\n', camera_matrix)
    print('Distortion coefficients:\n', dist_coeffs)
    print(f'Saved: {args.camera_matrix_out}, {args.dist_coeffs_out}, {args.report_out}')


if __name__ == '__main__':
    main()
