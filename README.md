# Drone Automation Using the Crazyflie 2.1+

Development of an experimental flight automation framework for the Bitcraze Crazyflie 2.1+ micro quadrotor using autonomous trajectory generation, onboard state estimation, and flight data logging.

## Overview

This repository contains software developed as part of an undergraduate mechanical engineering research project at the Illinois Institute of Technology. The project focuses on establishing repeatable autonomous flight experiments for a Crazyflie 2.1+ microdrone and logging onboard state estimates for later trajectory analysis.

The current implementation focuses on:

- Autonomous Crazyflie 2.1+ flight control
- Figure-eight trajectory generation
- Onboard Extended Kalman Filter (EKF) state estimation
- Flight data logging
- CSV export for post-processing and trajectory comparison
- Baseline flight experiments to support future Model Predictive Control (MPC) evaluation

External vision-based validation is handled in a companion repository:

**OpenCV-Tracking:** https://github.com/emora97/OpenCV-Tracking

That repository contains the camera calibration, ArUco tracking, markerless tracking, and external trajectory comparison pipeline.

---

## Features

- Autonomous takeoff, trajectory execution, and landing
- Figure-eight reference trajectory generation
- Position and state logging from the Crazyflie onboard estimator
- CSV output for post-processing
- Baseline data collection for future MPC comparison
- Support for Flow Deck v2-based localization
- Research-oriented structure for repeatable flight testing

---

## Repository Structure

```text
.
├── src/
│   └── Crazyflie flight control, trajectory, and logging scripts
│
├── data/
│   └── Flight logs and experimental data
│
├── docs/
│   └── Supporting documentation
│
├── media/
│   └── Images, overlays, and visual examples
│
├── requirements.txt
└── README.md
