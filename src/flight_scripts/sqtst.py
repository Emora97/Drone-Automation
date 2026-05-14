import time
from config import RADIO_URI, CACHE_DIR

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander


def main():
    cflib.crtp.init_drivers(enable_debug_driver=False)

    with SyncCrazyflie(RADIO_URI, cf=Crazyflie(rw_cache=CACHE_DIR)) as scf:
        # This wrapper keeps a fixed height unless you change it
        with PositionHlCommander(
            scf,
            default_height=0.35,
            controller=PositionHlCommander.CONTROLLER_PID,
        ) as pc:
            time.sleep(1.0)

            d = 0.50  # 20 cm
            t = 2.0   # seconds per move

            print("Forward (+x)")
            pc.go_to(d, 0.0, 0.35, t)
            time.sleep(t + 0.3)

            print("Back to origin")
            pc.go_to(0.0, 0.0, 0.35, t)
            time.sleep(t + 0.3)

            print("Left/Right (+y)")
            pc.go_to(0.0, d, 0.35, t)
            time.sleep(t + 0.3)

            print("Back to origin")
            pc.go_to(0.0, 0.0, 0.35, t)
            time.sleep(t + 0.3)

            print("Landing")
            pc.land()
            time.sleep(2.0)


if __name__ == "__main__":
    main()
