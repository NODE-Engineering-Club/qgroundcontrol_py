from pwm_controller import PWMController
import time

# Change port if needed
pwm = PWMController('/dev/ttyACM0')

print("Turning LEFT...")
pwm.steer_left()
time.sleep(2)

print("Turning RIGHT...")
pwm.steer_right()
time.sleep(2)

print("Going FORWARD...")
pwm.go_forward()
time.sleep(2)

print("STOPPING...")
pwm.stop_all()
