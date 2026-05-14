# Crazyflie Trajectory Validation
To install required libraries and dependencies, follow the link to Bitcraze's tutorial below:
https://www.bitcraze.io/documentation/tutorials/getting-started-with-crazyflie-2-x/#controlling-the-crazyflie

This project documents figure-8 trajectory testing using a Crazyflie 2.1+ microdrone with Flowdeck v2 onboard state estimation. Python scripts are used for flight control, telemetry logging, and OpenCV-based trajectory visualization.

## Hardware
- Crazyflie 2.1+
- Flowdeck v2
- Crazyradio 2.0

## Software
- Python
- cflib
- OpenCV
- pandas
- matplotlib

## Project Goals
- Implement figure-8 trajectory tracking
- Log onboard position and velocity estimates
- Visualize flight data against commanded trajectories
- Evaluate limitations of onboard state estimation

## Current Limitations
OpenCV overlays are used for visualization and validation support, not calibrated external ground truth.

## Future Work
- Improve trajectory tracking
- Compare onboard estimates against external ground truth
- Explore MPC-based control frameworks
