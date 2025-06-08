from pymavlink import mavutil
import time

class QGCMissionController:
    def __init__(self, connection_str='/dev/ttyACM0', baud=57600):
        print("[QGC] Connecting to Pixhawk...")
        self.master = mavutil.mavlink_connection(connection_str, baud=baud)
        self.master.wait_heartbeat()
        print("[QGC] Connected to Pixhawk.")

    def pause_mission(self):
        print("[QGC] Pausing mission...")
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_DO_PAUSE_CONTINUE,
            0,
            1, 0, 0, 0, 0, 0  # param1 = 1 → Pause
        )
        time.sleep(1)

    def resume_mission(self):
        print("[QGC] Resuming mission...")
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_DO_PAUSE_CONTINUE,
            0,
            0, 0, 0, 0, 0, 0  # param1 = 0 → Resume
        )
        time.sleep(1)

    def get_mode(self):
        print("[QGC] Checking current mode...")
        self.master.mav.request_data_stream_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL,
            1, 1
        )
        msg = self.master.recv_match(type='HEARTBEAT', blocking=True)
        mode = mavutil.mode_string_v10(msg)
        print(f"[QGC] Mode: {mode}")
        return mode
