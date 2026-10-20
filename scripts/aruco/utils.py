from __future__ import annotations

from datetime import datetime
from pathlib import Path
import cv2


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def timestamp_filename(prefix: str = 'img', suffix: str = '.jpg') -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{suffix}"


def draw_text_block(frame, lines, start=(20, 30), line_gap=28, color=(0, 255, 0)):
    x, y = start
    for i, line in enumerate(lines):
        pos = (x, y + i * line_gap)
        cv2.putText(frame, str(line), pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, str(line), pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)


def draw_info(frame, result, y=40):
    marker_id = result.get('id', '?')
    depth_z = result.get('depth_z', 0.0)
    distance_3d = result.get('distance_3d', 0.0)
    text = f"ID: {marker_id} | Z: {depth_z:.3f} m | 3D: {distance_3d:.3f} m"
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


def draw_marker_info(frame, result, y=40):
    marker_id = result.get('id', '?')
    tx = result.get('tx', 0.0)
    tz = result.get('tz', 0.0)
    area = result.get('area_px', 0.0)
    text = f"ID:{marker_id} tx:{tx:+.3f}m tz:{tz:.3f}m area:{area:.0f}px"
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)


def draw_frame_center(frame):
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (255, 255, 255), 1)
    cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (255, 255, 255), 1)


def draw_overlay(frame, lines, origin=(20, 30), line_gap=24, color=(255, 255, 255)):
    draw_text_block(frame, lines, start=origin, line_gap=line_gap, color=color)
