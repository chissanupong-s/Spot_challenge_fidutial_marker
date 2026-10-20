from __future__ import annotations

import argparse
from pathlib import Path
import cv2
import cv2.aruco as aruco

from scripts.aruco.detector import ARUCO_DICTIONARIES
from scripts.aruco.utils import ensure_dir


def parse_args():
    parser = argparse.ArgumentParser(description='Generate an ArUco marker image.')
    parser.add_argument('--dictionary', default='DICT_6X6_250', choices=sorted(ARUCO_DICTIONARIES.keys()))
    parser.add_argument('--marker-id', type=int, default=0)
    parser.add_argument('--marker-size-px', type=int, default=400)
    parser.add_argument('--output', default='assets/markers/marker_0.png')
    return parser.parse_args()


def main():
    args = parse_args()
    aruco_dict = aruco.getPredefinedDictionary(ARUCO_DICTIONARIES[args.dictionary])

    output_path = Path(args.output)
    ensure_dir(output_path.parent)

    if hasattr(aruco, 'generateImageMarker'):
        image = aruco.generateImageMarker(aruco_dict, args.marker_id, args.marker_size_px)
    else:
        image = aruco.drawMarker(aruco_dict, args.marker_id, args.marker_size_px)

    cv2.imwrite(str(output_path), image)
    print(f'Saved marker to: {output_path}')
    print('Measure the whole printed black marker side before using it as --marker-length.')


if __name__ == '__main__':
    main()
