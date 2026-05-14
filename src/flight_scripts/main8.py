import csv
import logging
import math
import time
from datetime import datetime
from pathlib import Path

from config import RADIO_URI, CACHE_DIR

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

logging.basicConfig(level=logging.ERROR)


# -----------------------------
# Simple file logger for telemetry
# -----------------------------
class CsvBlockLogger:
    def __init__(self, run_dir: Path, filename: str):
        self.path = run_dir / filename
        self.file = open(self.path, "w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        self.header_written = False
        self.keys = []

    def callback(self, timestamp, data, LogConf):
        if not self.header_written:
            self.keys = list(data.keys())
            self.writer.writerow(["cf_timestamp_ms"] + self.keys)
            self.header_written = True

        row = [timestamp] + [data.get(k, "") for k in self.keys]
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        self.file.close()


# -----------------------------
# Row logger for reference vs state
# -----------------------------
class CsvRowLogger:
    def __init__(self, run_dir: Path, filename: str, header):
        self.path = run_dir / filename
        self.file = open(self.path, "w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        self.writer.writerow(header)
        self.file.flush()

    def write_row(self, row):
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        self.file.close()


# -----------------------------
# Utility functions
# -----------------------------
def pulse_kalman_reset(cf) -> None:
    cf.param.set_value("stabilizer.estimator", "2")  #0=comp, 1=ext Kalman, 3=unscended kalman
    cf.param.set_value("kalman.resetEstimation", "1") #0=default; 1=use robust TDOA method
    time.sleep(0.1)
    cf.param.set_value("kalman.resetEstimation", "0")
    time.sleep(1.5)


def safe_arm(cf) -> None:
    try:
        cf.platform.send_arming_request(True)
        time.sleep(0.5)
    except Exception:
        pass


def ramp_z_hover(cf, z0: float, z1: float, duration_s: float, dt: float = 0.05) -> None:
    """
    Uses hover setpoints only for vertical takeoff/landing.
    vx, vy, yawrate are zero during the ramp.
    """
    steps = max(1, int(duration_s / dt))
    for i in range(steps + 1):
        z = z0 + (z1 - z0) * (i / steps)
        cf.commander.send_hover_setpoint(0.0, 0.0, 0.0, z)
        time.sleep(dt)


def hold_hover(cf, z: float, duration_s: float, dt: float = 0.05) -> None:
    """
    Holds altitude using hover setpoints before/after the world-frame maneuver.
    """
    t0 = time.time()
    while (time.time() - t0) < duration_s:
        cf.commander.send_hover_setpoint(0.0, 0.0, 0.0, z)
        time.sleep(dt)


# -----------------------------
# TOC helpers
# -----------------------------
def flatten_toc(cf):
    names = []
    for group, members in cf.log.toc.toc.items():
        for name in members.keys():
            names.append(f"{group}.{name}")
    return sorted(names)


def save_available_log_vars(cf, run_dir: Path):
    with open(run_dir / "available_log_vars.txt", "w", encoding="utf-8") as f:
        for name in flatten_toc(cf):
            f.write(name + "\n")


def build_log_block(cf, name: str, period_ms: int, variables):
    log_conf = LogConfig(name=name, period_in_ms=period_ms)
    added = []
    skipped = []

    for var_name, var_type in variables:
        elem = cf.log.toc.get_element_by_complete_name(var_name)
        if elem is not None:
            log_conf.add_variable(var_name, var_type)
            added.append(var_name)
        else:
            skipped.append(var_name)

    return log_conf, added, skipped


# 
# -----------------------------
def figure8_world_single_logged(
    scf: SyncCrazyflie,
    run_dir: Path,
    width_m: float,
    depth_m: float,
    period_s: float,
    vmax_xy: float = 0.4,
    dt: float = 0.02,
) -> None:
    """
    Rotated world-frame figure-8:
      - one single cycle only
      - no recentering term
      - big lobes on WORLD Y
      - small crossing motion on WORLD X

    If your previous world-frame script still looked front/back,
    this rotates the trajectory by 90 degrees.

    Position reference:
      x_ref = 0.5 * depth_m * sin(2 w t)
      y_ref = 0.5 * width_m * sin(w t)

    Velocity reference:
      vx_ref = depth_m * w * cos(2 w t)
      vy_ref = 0.5 * width_m * w * cos(w t)
    """
    cf = scf.cf
    w = 2.0 * math.pi / period_s
    ay = 0.5 * width_m

    ref_logger = CsvRowLogger(
        run_dir,
        "figure8_reference_vs_state.csv",
        header=[
            "t_s",
            "x_ref_world_m",
            "y_ref_world_m",
            "vx_ref_world_mps",
            "vy_ref_world_mps",
            "x_est_m",
            "y_est_m",
            "z_est_m",
            "vx_est_mps",
            "vy_est_mps",
            "yaw_deg",
        ],
    )

    lg = LogConfig(name="fig8_world", period_in_ms=max(10, int(dt * 1000)))
    wanted_vars = [
        ("stateEstimate.x", "float"),
        ("stateEstimate.y", "float"),
        ("stateEstimate.z", "float"),
        ("kalman.stateX", "float"),
        ("kalman.stateY", "float"),
        ("stabilizer.yaw", "float"),
    ]

    added = []
    for var_name, var_type in wanted_vars:
        elem = cf.log.toc.get_element_by_complete_name(var_name)
        if elem is not None:
            lg.add_variable(var_name, var_type)
            added.append(var_name)

    if "stateEstimate.x" not in added or "stateEstimate.y" not in added:
        ref_logger.close()
        raise RuntimeError("Required stateEstimate.x/y variables are missing from log TOC.")

    t0 = time.time()

    try:
        with SyncLogger(scf, lg) as logger:
            for _, d, _ in logger:
                t = time.time() - t0
                if t > period_s:
                    break

                # 90-degree-rotated WORLD-frame figure 8
                # Big lobes are now on WORLD Y
                x_ref = 0.5 * depth_m * math.sin(2.0 * w * t)
                y_ref = ay * math.sin(w * t)

                vx_ref = depth_m * w * math.cos(2.0 * w * t)
                vy_ref = ay * w * math.cos(w * t)

                vx_cmd = max(-vmax_xy, min(vmax_xy, vx_ref))
                vy_cmd = max(-vmax_xy, min(vmax_xy, vy_ref))

                cf.commander.send_velocity_world_setpoint(vx_cmd, vy_cmd, 0.0, 0.0)

                x_est = float(d["stateEstimate.x"]) if "stateEstimate.x" in d else float("nan")
                y_est = float(d["stateEstimate.y"]) if "stateEstimate.y" in d else float("nan")
                z_est = float(d["stateEstimate.z"]) if "stateEstimate.z" in d else float("nan")
                vx_est = float(d["kalman.stateX"]) if "kalman.stateX" in d else float("nan")
                vy_est = float(d["kalman.stateY"]) if "kalman.stateY" in d else float("nan")
                yaw_deg = float(d["stabilizer.yaw"]) if "stabilizer.yaw" in d else float("nan")

                ref_logger.write_row([
                    t,
                    x_ref,
                    y_ref,
                    vx_cmd,
                    vy_cmd,
                    x_est,
                    y_est,
                    z_est,
                    vx_est,
                    vy_est,
                    yaw_deg,
                ])

                time.sleep(dt)

    finally:
        ref_logger.close()


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    Z_HOVER = 0.30
    WIDTH_M = 0.70          # dominant span
    DEPTH_M = 0.30          # smaller crossing span
    PERIOD_S = 8.5
    VMAX_XY = 0.75
    DT = 0.02
    TAKEOFF_RAMP_S = 2.0
    LAND_RAMP_S = 3.0
    LOG_PERIOD_MS = 25

    run_dir = Path("runs") / datetime.now().strftime("%Y-%m-%d_%H%M%S_figure8_world_rotated")
    run_dir.mkdir(parents=True, exist_ok=True)

    cflib.crtp.init_drivers(enable_debug_driver=False)

    with SyncCrazyflie(RADIO_URI, cf=Crazyflie(rw_cache=CACHE_DIR)) as scf:
        cf = scf.cf

        save_available_log_vars(cf, run_dir)

        # Force x-mode off so client-side axis remapping does not interfere
        try:
            cf.commander.set_client_xmode(False)
        except Exception:
            pass

        state_vars = [
            ("stateEstimate.x", "float"),
            ("stateEstimate.y", "float"),
            ("stateEstimate.z", "float"),
            ("stabilizer.roll", "float"),
            ("stabilizer.pitch", "float"),
            ("stabilizer.yaw", "float"),
        ]

        aux_vars = [
            ("kalman.statePX", "float"),
            ("kalman.statePY", "float"),
            ("kalman.statePZ", "float"),
            ("range.front", "uint16_t"),
            ("range.back", "uint16_t"),
            ("range.left", "uint16_t"),
            ("range.right", "uint16_t"),
            ("range.zrange", "uint16_t"),
            ("motion.deltaX", "int16_t"),
            ("motion.deltaY", "int16_t"),
        ]

        state_conf, state_added, state_skipped = build_log_block(
            cf, "state", LOG_PERIOD_MS, state_vars
        )
        aux_conf, aux_added, aux_skipped = build_log_block(
            cf, "aux", LOG_PERIOD_MS, aux_vars
        )

        print("state added:", state_added)
        print("state skipped:", state_skipped)
        print("aux added:", aux_added)
        print("aux skipped:", aux_skipped)

        state_logger = CsvBlockLogger(run_dir, "state_log.csv")
        aux_logger = CsvBlockLogger(run_dir, "aux_log.csv")

        if state_added:
            cf.log.add_config(state_conf)
            state_conf.data_received_cb.add_callback(state_logger.callback)

        if aux_added:
            cf.log.add_config(aux_conf)
            aux_conf.data_received_cb.add_callback(aux_logger.callback)

        try:
            try:
                bcflow2 = cf.param.get_value("deck.bcFlow2")
                bcflow = cf.param.get_value("deck.bcFlow")
                print(f"deck.bcFlow2={bcflow2}  deck.bcFlow={bcflow}")
            except Exception as e:
                print("Warning: could not read deck params:", e)

            pulse_kalman_reset(cf)
            safe_arm(cf)

            if state_added:
                state_conf.start()
            if aux_added:
                aux_conf.start()

            # Take off and settle
            ramp_z_hover(cf, 0.0, Z_HOVER, TAKEOFF_RAMP_S)
            hold_hover(cf, Z_HOVER, duration_s=1.0)

            # One single rotated WORLD-frame figure 8
            figure8_world_single_logged(
                scf=scf,
                run_dir=run_dir,
                width_m=WIDTH_M,
                depth_m=DEPTH_M,
                period_s=PERIOD_S,
                vmax_xy=VMAX_XY,
                dt=DT,
            )

            # Re-enter hover mode before landing
            hold_hover(cf, Z_HOVER, duration_s=1.0)
            ramp_z_hover(cf, Z_HOVER, 0.0, LAND_RAMP_S)

            cf.commander.send_stop_setpoint()
            cf.commander.send_notify_setpoint_stop()

        finally:
            if state_added:
                state_conf.stop()
            if aux_added:
                aux_conf.stop()

            state_logger.close()
            aux_logger.close()

    print(f"Saved logs to: {run_dir}")


if __name__ == "__main__":
    main()