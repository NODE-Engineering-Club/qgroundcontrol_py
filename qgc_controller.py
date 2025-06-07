# qgc_controller.py
from pymavlink import mavutil
import time

def connect_to_pixhawk(port="/dev/ttyACM0", baud=57600):
    try:
        master = mavutil.mavlink_connection(port, baud=baud)
        master.wait_heartbeat()
        print(f"✅ Connected to Pixhawk on {port}")
        return master
    except Exception as e:
        print(f"❌ Could not connect to Pixhawk: {e}")
        return None

def pause_mission(port="/dev/ttyACM0"):
    master = connect_to_pixhawk(port)
    if master:
        master.mav.command_long_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_CMD_DO_PAUSE_CONTINUE,
            0,
            1, 0, 0, 0, 0, 0, 0  # Pause mission
        )
        print("⏸️ Mission paused.")
        master.close()

def resume_mission(port="/dev/ttyACM0"):
    master = connect_to_pixhawk(port)
    if master:
        master.mav.command_long_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_CMD_DO_PAUSE_CONTINUE,
            0,
            0, 0, 0, 0, 0, 0, 0  # Resume mission
        )
        print("▶️ Mission resumed.")
        master.close()
