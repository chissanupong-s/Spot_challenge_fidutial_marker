from __future__ import annotations

from pathlib import Path
import numpy as np


CALIBRATION_ROOT = Path('assets/calibration')

# Native stream size of each camera. The Tello forward camera streams 960x720 (4:3);
# its frames must not be resized, or the calibration no longer matches the pixels.
NATIVE_FRAME_SIZE = {
    'webcam': (1280, 720),
    'tello': (960, 720),
    # Downward camera (Tello EDU / TT firmware): grayscale, low resolution
    'tello_down': (320, 240),
}


def calibration_paths(camera: str) -> tuple[Path, Path]:
    folder = CALIBRATION_ROOT / camera
    return folder / 'camera_matrix.npy', folder / 'dist_coeffs.npy'


def save_calibration(camera_matrix: np.ndarray,
                     dist_coeffs: np.ndarray,
                     camera_matrix_path: str | Path,
                     dist_coeffs_path: str | Path) -> None:
    np.save(str(camera_matrix_path), camera_matrix)
    np.save(str(dist_coeffs_path), dist_coeffs)


def load_calibration(camera_matrix_path: str | Path, dist_coeffs_path: str | Path):
    for path in (camera_matrix_path, dist_coeffs_path):
        if not Path(path).exists():
            raise FileNotFoundError(
                f'Calibration file not found: {path}\n'
                'Capture chessboard images and run calibrate_camera for this camera first.'
            )
    camera_matrix = np.load(str(camera_matrix_path))
    dist_coeffs = np.load(str(dist_coeffs_path))
    return camera_matrix, dist_coeffs


def calibration_mismatch(camera_matrix: np.ndarray, frame_shape, tolerance: float = 0.15) -> str | None:
    """Return a warning if the optical center is far from the frame center.

    That usually means the calibration was made at a different resolution
    (or with a different camera) than the frames being processed.
    """
    h, w = frame_shape[:2]
    cx, cy = float(camera_matrix[0, 2]), float(camera_matrix[1, 2])
    if abs(cx - w / 2) > tolerance * w or abs(cy - h / 2) > tolerance * h:
        return (f'Calibration optical center ({cx:.0f}, {cy:.0f}) does not fit a {w}x{h} frame. '
                'Distances will be wrong - recalibrate at this resolution.')
    return None
