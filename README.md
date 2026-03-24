# Dobot Magician Lite — YOLO Object Detection + Palletizing

**RAS 545 · Robotic and Autonomous Systems Lab 3 · Arizona State University · Fall 2025**

> Autonomous perception-driven palletizing: YOLOv8 classifies objects in real time via a mounted camera, and the Dobot Magician Lite picks and sorts them into the correct pallet using a suction cup.

---

## Demo

[![Lab 3 Demo](https://img.youtube.com/vi/ZaWCXo_jxXU/0.jpg)](https://youtube.com/shorts/ZaWCXo_jxXU)

---

## Overview

The Dobot Magician Lite (Serial: `DT15-2311-1432`) uses a camera mounted above the end-effector to detect objects placed in a fixed pickup zone. YOLOv8s classifies each object into one of two categories — **food** or **vehicle** — and the robot autonomously picks it up and places it in the corresponding pallet (A or B), then returns home to repeat the cycle.

### Detection logic

| YOLO Label | Category | Destination |
|---|---|---|
| `apple`, `banana`, `sandwich`, `pizza`, `cake` | Food | Pallet A |
| `car`, `truck`, `bus`, `motorbike`, `bicycle` | Vehicle | Pallet B |

---

## Repository Structure
```
.
├── camera_palletization.py          # Main YOLO + Dobot integration script
├── Lab_3_RAS_vishal.pdf             # Full lab report (IEEE/IJRR format)
└── README.md
```

---

## System Architecture
```
Camera (cv2) → YOLOv8s Inference → Class Detection
                                         ↓
                              Food → Pallet A
                              Vehicle → Pallet B
                                         ↓
                         Dobot: Home → Pickup → Intermediate → Drop → Home
```

---

## Technical Details

### Robot States

| State | X (mm) | Y (mm) | Z (mm) | R (°) |
|---|---|---|---|---|
| Home | 240.000 | 0.000 | 150.000 | −8.881 |
| Pickup | 306.420 | −82.706 | −55.166 | −15.104 |
| Intermediate | 193.526 | 22.005 | 35.189 | 6.487 |
| Pallet A (Food) | 210.180 | −233.553 | 24.075 | −46.766 |
| Pallet B (Vehicle) | 303.931 | 220.869 | 26.487 | 36.006 |

### Motion Sequence
```
Home → Pickup (descend) → suck(True) → Intermediate (lift)
     → Pallet A or B (drop) → suck(False) → Home → repeat
```

### Key Parameters

| Parameter | Value |
|---|---|
| Model | YOLOv8s (`yolov8s.pt`) |
| Camera index | `/dev/video2` |
| Resolution | 640 × 480 |
| Robot port | `/dev/ttyACM0` |
| Speed | 100, 100 |
| Home tolerance | ±10 mm |

---

## Setup & Usage

### Requirements
```bash
pip install pydobot2 ultralytics opencv-python
sudo apt install v4l-utils ffmpeg
```

### Permissions
```bash
sudo usermod -a -G dialout $USER
v4l2-ctl --list-devices
ls /dev/tty*
```

### Run
```bash
python camera_palletization.py
```

- The robot homes on startup, then waits at home between each cycle
- Live camera feed shows YOLO bounding boxes and detection status
- Press **`q`** to quit cleanly — the `finally` block closes the camera and serial connection

### Update coordinates for your setup
```python
home_coordinates         = [239.999, 0.0, 150.0, -8.881]
intermediate_coordinates = [193.526, 22.005, 35.189, 6.487]
pickup_coordinates       = [306.420, -82.706, -55.166, -15.104]
palleteA_coordinates     = [210.180, -233.553, 24.075, -46.766]
palleteB_coordinates     = [303.931, 220.869, 26.487, 36.006]
```

---

## Lessons Learned

- Camera and robot coordinate calibration is critical — even a 5 mm offset causes consistent misses at the pickup zone
- Lighting significantly affects YOLO detection reliability; a uniform white surface gave the best contrast
- The `is_home()` check with ±10 mm tolerance prevents the robot from attempting a new pick cycle mid-motion
- Camera must be released (`cap.release()`) before robot motion and reopened after — USB bandwidth conflicts caused frame drops otherwise

---

## Course Info

- **Course:** RAS 545 — Robotic and Autonomous Systems Lab
- **Instructor:** Prof. Sangram Redkar
- **Lab Charge:** Sai Srinivas Tatwik Meesala · Rajesh S Aouti
- **University:** Arizona State University, Tempe AZ
- **Semester:** Fall 2025
- **Grade:** 10 / 10
