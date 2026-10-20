from __future__ import annotations

import cv2
import cv2.aruco as aruco
import numpy as np


ARUCO_DICTIONARIES = {
    'DICT_4X4_50': aruco.DICT_4X4_50,
    'DICT_4X4_100': aruco.DICT_4X4_100,
    'DICT_4X4_250': aruco.DICT_4X4_250,
    'DICT_4X4_1000': aruco.DICT_4X4_1000,
    'DICT_5X5_50': aruco.DICT_5X5_50,
    'DICT_5X5_100': aruco.DICT_5X5_100,
    'DICT_5X5_250': aruco.DICT_5X5_250,
    'DICT_5X5_1000': aruco.DICT_5X5_1000,
    'DICT_6X6_50': aruco.DICT_6X6_50,
    'DICT_6X6_100': aruco.DICT_6X6_100,
    'DICT_6X6_250': aruco.DICT_6X6_250,
    'DICT_6X6_1000': aruco.DICT_6X6_1000,
    'DICT_7X7_50': aruco.DICT_7X7_50,
    'DICT_7X7_100': aruco.DICT_7X7_100,
    'DICT_7X7_250': aruco.DICT_7X7_250,
    'DICT_7X7_1000': aruco.DICT_7X7_1000,
    'DICT_ARUCO_ORIGINAL': aruco.DICT_ARUCO_ORIGINAL,
}


class ArucoDistanceDetector:
    def __init__(self, marker_length=0.05,
                 dictionary=aruco.DICT_6X6_250,
                 allowed_ids=None):
        self.marker_length = float(marker_length)
        self.allowed_ids = set(allowed_ids) if allowed_ids is not None else None

        self.aruco_dict = aruco.getPredefinedDictionary(dictionary)
        self.detector = aruco.ArucoDetector(
            self.aruco_dict,
            aruco.DetectorParameters()
        )

        self.obj_points = np.array([
            [-self.marker_length / 2,  self.marker_length / 2, 0],
            [ self.marker_length / 2,  self.marker_length / 2, 0],
            [ self.marker_length / 2, -self.marker_length / 2, 0],
            [-self.marker_length / 2, -self.marker_length / 2, 0]
        ], dtype=np.float32)

    def detect(self, frame, camera_matrix=None, dist_coeffs=None):
        """Detect markers. Pose fields (rvec, tvec, tx, ...) are only filled when a calibration is given."""
        corners, ids, _ = self.detector.detectMarkers(frame)
        results = []

        if ids is None:
            return results, [], None

        filtered_corners = []
        filtered_ids = []

        for marker_id, c in zip(ids.flatten(), corners):
            marker_id = int(marker_id)
            if self.allowed_ids is not None and marker_id not in self.allowed_ids:
                continue

            img_points = c[0].astype(np.float32)
            center_x = float(np.mean(img_points[:, 0]))
            center_y = float(np.mean(img_points[:, 1]))
            area_px = float(cv2.contourArea(img_points))

            if camera_matrix is None:
                filtered_corners.append(c)
                filtered_ids.append([marker_id])
                results.append({
                    'id': marker_id,
                    'center_px': (center_x, center_y),
                    'area_px': area_px,
                    'corners': img_points,
                })
                continue

            ok, rvec, tvec = cv2.solvePnP(
                self.obj_points,
                img_points,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_IPPE_SQUARE,
            )
            if not ok:
                continue

            tx, ty, tz = tvec.flatten()

            filtered_corners.append(c)
            filtered_ids.append([marker_id])
            results.append({
                'id': marker_id,
                'rvec': rvec,
                'tvec': tvec,
                'tx': float(tx),
                'ty': float(ty),
                'tz': float(tz),
                'depth_z': float(tz),
                'distance_3d': float(np.linalg.norm(tvec)),
                'center_px': (center_x, center_y),
                'area_px': area_px,
                'corners': img_points,
            })

        if filtered_ids:
            filtered_ids = np.array(filtered_ids, dtype=np.int32)
        else:
            filtered_ids = None
            filtered_corners = []

        return results, filtered_corners, filtered_ids
