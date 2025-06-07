from pymavlink import mavutil
import time

class PWMController:
    def __init__(self, connection_str='/dev/ttyACM0', baud=57600):
        print("[PWM] Connecting to Pixhawk...")
        self.master = mavutil.mavlink_connection(connection_str, baud=baud)
        self.master.wait_heartbeat()
        print("[PWM] Connected to Pixhawk.")

    def send_pwm(self, channel, pwm_value):
        print(f"[PWM] Setting channel {channel} to {pwm_value}")
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
            0,
            channel,       # Servo output channel (1-based index)
            pwm_value,     # PWM value (1100-1900 typical)
            0, 0, 0, 0, 0
        )
        time.sleep(0.1)

    def steer_left(self):
        print("[PWM] Steer LEFT")
        self.send_pwm(1, 1100)  # Rear left motor reverse
        self.send_pwm(3, 1500)  # Front motor neutral

    def steer_right(self):
        print("[PWM] Steer RIGHT")
        self.send_pwm(1, 1900)  # Rear left motor forward
        self.send_pwm(3, 1500)  # Front motor neutral

    def go_forward(self):
        print("[PWM] Forward")
        self.send_pwm(1, 1500)
        self.send_pwm(3, 1900)

    def stop_all(self):
        print("[PWM] STOP")
        self.send_pwm(1, 1500)
        self.send_pwm(3, 1500)
