# Spot Challenge - Fiducial Marker Test Kit

Camera calibration and ArUco marker test for the laptop webcam and the Tello downward camera.

## How to download

1. Click the green **"<> Code"** button at the top of this page.
2. Click **"Download ZIP"**.
3. Unzip it (Windows: right-click -> **Extract All**; Ubuntu: right-click -> **Extract Here**).
4. Open the folder `Spot_challenge_fidutial_marker-main`.

## Start here

Open the guide for your computer and follow it step by step:

- Windows: [GUIDE_Windows.pdf](GUIDE_Windows.pdf) ([text version](GUIDE_Windows.md))
- Ubuntu: [GUIDE_Ubuntu.pdf](GUIDE_Ubuntu.pdf) ([text version](GUIDE_Ubuntu.md))

## What is in this folder

| Folder / file | What it is |
|---|---|
| `GUIDE_Windows.pdf`, `GUIDE_Ubuntu.pdf` | Step-by-step guide |
| `print/chessboard_10x7_21mm_A4.pdf` | Chessboard to print (10 x 7 squares, 21 mm) |
| `print/aruco_DICT_6X6_250_id0-2_150mm_A4.pdf` | ArUco markers ID 0, 1, 2 (DICT_6X6_250, 150 mm) |
| `scripts/` | The programs (do not change) |
| `requirements.txt` | List of libraries to install |

## Values

- Chessboard: 10 x 7 squares = 9 x 6 inner corners, square = 21 mm
- ArUco dictionary (family): DICT_6X6_250, IDs 0, 1, 2, black square = 150 mm

The drone never takes off with these programs.
