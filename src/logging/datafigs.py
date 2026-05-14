from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ---------------- DISPLAY MAPPING ----------------
# Match the poster/snip convention:
# horizontal display axis <- world y (lateral)
# vertical display axis   <- world x (forward/back)
swap_xy_for_display = True
flip_display_x = True
flip_display_y = False
# -------------------------------------------------


def load_csv(csv_path: str | Path) -> pd.DataFrame:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    return pd.read_csv(csv_path)


def validate_columns(df: pd.DataFrame, required_cols: list[str]) -> None:
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns:\n"
            + "\n".join(missing)
            + f"\n\nAvailable columns:\n{list(df.columns)}"
        )


def compute_errors(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Raw world-frame errors
    df["x_err_m"] = df["x_est_m"] - df["x_ref_world_m"]
    df["y_err_m"] = df["y_est_m"] - df["y_ref_world_m"]
    df["pos_err_m"] = np.sqrt(df["x_err_m"]**2 + df["y_err_m"]**2)

    df["vx_err_mps"] = df["vx_est_mps"] - df["vx_ref_world_mps"]
    df["vy_err_mps"] = df["vy_est_mps"] - df["vy_ref_world_mps"]
    df["vel_err_mps"] = np.sqrt(df["vx_err_mps"]**2 + df["vy_err_mps"]**2)

    return df


def print_summary(df: pd.DataFrame) -> None:
    print("\n=== Summary ===")
    print(f"Samples: {len(df)}")
    print(f"Duration: {df['t_s'].iloc[-1] - df['t_s'].iloc[0]:.3f} s")
    print(f"Mean position error: {df['pos_err_m'].mean():.4f} m")
    print(f"Max position error:  {df['pos_err_m'].max():.4f} m")
    print(f"RMSE position error: {np.sqrt(np.mean(df['pos_err_m']**2)):.4f} m")
    print(f"Mean velocity error: {df['vel_err_mps'].mean():.4f} m/s")
    print(f"Max velocity error:  {df['vel_err_mps'].max():.4f} m/s")

    if "z_est_m" in df.columns:
        print(f"Mean z: {df['z_est_m'].mean():.4f} m")
        print(f"Min z:  {df['z_est_m'].min():.4f} m")
        print(f"Max z:  {df['z_est_m'].max():.4f} m")

    if "yaw_deg" in df.columns:
        print(f"Yaw min/max: {df['yaw_deg'].min():.2f} / {df['yaw_deg'].max():.2f} deg")


def map_display_axes(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert raw world-frame axes to display axes that match the snip overlays.

    Raw meaning:
      a = x-like quantity (forward/back)
      b = y-like quantity (lateral)

    Display meaning:
      horizontal = lateral
      vertical   = forward/back
    """
    a = np.asarray(a)
    b = np.asarray(b)

    if swap_xy_for_display:
        disp_x = b.copy()
        disp_y = a.copy()
    else:
        disp_x = a.copy()
        disp_y = b.copy()

    if flip_display_x:
        disp_x = -disp_x
    if flip_display_y:
        disp_y = -disp_y

    return disp_x, disp_y


def plot_xy_trajectory(df: pd.DataFrame) -> None:
    x_ref_disp, y_ref_disp = map_display_axes(df["x_ref_world_m"], df["y_ref_world_m"])
    x_est_disp, y_est_disp = map_display_axes(df["x_est_m"], df["y_est_m"])

    plt.figure(figsize=(7, 7))
    plt.plot(x_ref_disp, y_ref_disp, label="Reference")
    plt.plot(x_est_disp, y_est_disp, label="Estimated")
    plt.xlabel("Y [m] (Lateral Position)")
    plt.ylabel("X [m] (Forward/Back Position)")
    plt.title("Figure-8 Trajectory: Reference vs Estimated")
    plt.axis("equal")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()


def plot_position_vs_time(df: pd.DataFrame) -> None:
    ref_dx, ref_dy = map_display_axes(df["x_ref_world_m"], df["y_ref_world_m"])
    est_dx, est_dy = map_display_axes(df["x_est_m"], df["y_est_m"])

    plt.figure(figsize=(10, 5))
    plt.plot(df["t_s"], ref_dx, label="y_ref")
    plt.plot(df["t_s"], est_dx, label="y_est")
    plt.plot(df["t_s"], ref_dy, label="x_ref")
    plt.plot(df["t_s"], est_dy, label="x_est")
    plt.xlabel("Time [s]")
    plt.ylabel("Position [m]")
    plt.title("Frame Position vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()


def plot_velocity_vs_time(df: pd.DataFrame) -> None:
    ref_vx_disp, ref_vy_disp = map_display_axes(df["vx_ref_world_mps"], df["vy_ref_world_mps"])
    est_vx_disp, est_vy_disp = map_display_axes(df["vx_est_mps"], df["vy_est_mps"])

    plt.figure(figsize=(10, 5))
    plt.plot(df["t_s"], ref_vx_disp, label="display_vx_ref")
    plt.plot(df["t_s"], est_vx_disp, label="display_vx_est")
    plt.plot(df["t_s"], ref_vy_disp, label="display_vy_ref")
    plt.plot(df["t_s"], est_vy_disp, label="display_vy_est")
    plt.xlabel("Time [s]")
    plt.ylabel("Velocity [m/s]")
    plt.title("Display-Frame Velocity vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()


def plot_position_error(df: pd.DataFrame) -> None:
    err_dx, err_dy = map_display_axes(df["x_err_m"], df["y_err_m"])

    plt.figure(figsize=(10, 5))
    plt.plot(df["t_s"], err_dx, label="x error")
    plt.plot(df["t_s"], err_dy, label="y error")
    plt.plot(df["t_s"], df["pos_err_m"], label="position error magnitude")
    plt.xlabel("Time [s]")
    plt.ylabel("Error [m]")
    plt.title("Estimated Position Error vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()


def plot_velocity_error(df: pd.DataFrame) -> None:
    err_vx_disp, err_vy_disp = map_display_axes(df["vx_err_mps"], df["vy_err_mps"])

    plt.figure(figsize=(10, 5))
    plt.plot(df["t_s"], err_vx_disp, label="vx error")
    plt.plot(df["t_s"], err_vy_disp, label="vy error")
    plt.plot(df["t_s"], df["vel_err_mps"], label="velocity error magnitude")
    plt.xlabel("Time [s]")
    plt.ylabel("Error [m/s]")
    plt.title("Estimated Velocity Error vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()


def plot_yaw(df: pd.DataFrame) -> None:
    if "yaw_deg" not in df.columns:
        return
    plt.figure(figsize=(10, 4))
    plt.plot(df["t_s"], df["yaw_deg"])
    plt.xlabel("Time [s]")
    plt.ylabel("Yaw [deg]")
    plt.title("Yaw vs Time")
    plt.grid(True)
    plt.tight_layout()


def plot_altitude(df: pd.DataFrame) -> None:
    if "z_est_m" not in df.columns:
        return
    plt.figure(figsize=(10, 4))
    plt.plot(df["t_s"], df["z_est_m"])
    plt.xlabel("Time [s]")
    plt.ylabel("Z [m]")
    plt.title("Estimated Altitude vs Time")
    plt.grid(True)
    plt.tight_layout()


def main():
    csv_path = "fig8_log.csv"

    df = load_csv(csv_path)

    required_cols = [
        "t_s",
        "x_ref_world_m",
        "y_ref_world_m",
        "vx_ref_world_mps",
        "vy_ref_world_mps",
        "x_est_m",
        "y_est_m",
        "vx_est_mps",
        "vy_est_mps",
    ]
    validate_columns(df, required_cols)

    df = compute_errors(df)
    print_summary(df)

    plot_xy_trajectory(df)
    plot_position_vs_time(df)
    plot_velocity_vs_time(df)
    plot_position_error(df)
    plot_velocity_error(df)
    plot_yaw(df)
    plot_altitude(df)

    plt.show()


if __name__ == "__main__":
    main()