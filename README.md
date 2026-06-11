# Drone Automation Using the Crazyflie 2.1+

Development of an experimental flight automation framework for the Bitcraze Crazyflie 2.1+ micro quadrotor using onboard state estimation, autonomous trajectory generation, and external computer vision tracking for validation.

## Overview

This repository contains the software developed as part of an undergraduate mechanical engineering research project at the Illinois Institute of Technology. The project investigates methods for establishing repeatable autonomous flight experiments and evaluating onboard localization accuracy through external vision-based tracking.

The current implementation focuses on:

- Autonomous figure-eight trajectory generation
- Onboard Extended Kalman Filter (EKF) state estimation
- Flight data logging
- External ArUco marker tracking with OpenCV (Separate repository, see OpenCV-Tracking)
- Markerless object tracking comparison
- Camera calibration and pose estimation
- Quantitative comparison between onboard and external localization methods

Future work includes the implementation and evaluation of lightweight Model Predictive Control (MPC) algorithms on resource-constrained aerial platforms.

---

## Features

- Autonomous Crazyflie 2.1+ flight control
- Figure-eight trajectory generation
- Position logging and CSV export
- OpenCV-based ArUco marker detection
- Markerless visual tracking pipeline
- Camera intrinsic calibration utilities
- Trajectory synchronization and comparison tools
- Error analysis and visualization scripts
- Publication-quality plotting utilities

---

## Repository Structure

```text
.
├── src/
│   ├── main.py
│   ├── calibration/
│   ├── logging/
│   ├── trajectories/
│   └── utilities/
│
├── data/
│   ├── logs/
│   ├── calibration/
│   └── output/
│
├── figures/
│
└── README.md
```


---

## Hardware

- Bitcraze Crazyflie 2.1+
- Flow Deck v2
- Crazyradio PA 2.0
- External overhead camera
- Printed ArUco markers
- Calibration checkerboard

---

## Software

- Python 3.x
- OpenCV
- NumPy
- Pandas
- Matplotlib
- cflib (Bitcraze Python Library)

---

## Installation

Clone the repository:

```bash
git clone https://github.com<emora97>/<Drone-Automation>.git
cd <Drone-Automation>
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Workflow

### 1. Camera Calibration

Generate camera intrinsic parameters using checkerboard images.

```bash
python camera_calibration.py
```

---

### 2. Autonomous Flight

Execute the Crazyflie flight script to generate the desired trajectory while logging onboard state estimates.

```bash
python main8.py
```

---

### 3. External Tracking

Process recorded video using either:

- ArUco marker tracking

```bash
python aruco_tracker.py
```

or

- Markerless tracking

```bash
python markerless_tracker.py
```

---

### 4. Trajectory Comparison

Synchronize onboard logs with external measurements and generate comparison plots.

```bash
python compare_tracking.py
```

---

## Output

Typical outputs include:

- Logged flight CSV files
- Camera calibration parameters
- Tracked trajectories
- Error statistics
- Position comparison plots
- Figure-eight trajectory visualizations

---

## Research Objectives

The goal of this project is to establish a low-cost experimental framework capable of:

- Evaluating onboard localization accuracy
- Comparing external vision-based tracking methods
- Quantifying flight performance during autonomous maneuvers
- Supporting future implementation of embedded Model Predictive Control (MPC)

---

## Future Improvements

- TinyMPC integration
- acados implementation
- Multi-camera motion capture
- Real-time ground truth feedback
- Additional autonomous trajectories
- Closed-loop visual localization

---

## Acknowledgments

This work was completed as part of undergraduate research in Mechanical Engineering at the Illinois Institute of Technology using the Bitcraze Crazyflie ecosystem and OpenCV computer vision libraries.

---

## License

This project is released under the MIT License unless otherwise specified.
