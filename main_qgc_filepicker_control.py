import os
import time
import cv2
import tkinter as tk
from tkinter import filedialog
from vision import visionNav
from pwm_controller import PWMController
from qgc_plan_converter import convert_csv_to_plan
from mission_logger import MissionLogger
import subprocess

# === CONFIG ===
CAMERA_INDEX = 0
MAVLINK_UDP = "udp:127.0.0.1:14551"
PLAN_OUTPUT = "mission.plan"
LOG_FILE_PATH = "mission_log.txt"
QGC_PATH = "/home/pi/QGroundControl.AppImage"  # Adjust if stored somewhere else

logger = MissionLogger()

def ask_for_csv_path():
    root = tk.Tk()
    root.withdraw()
    print(" Select GPS CSV file or press Cancel to skip.")
    file_path = filedialog.askopenfilename(
        title="Select GPS CSV File (Optional)",
        filetypes=[("CSV Files", "*.csv")]
    )
    if not file_path:
        print("⚠️ CSV skipped. No mission.plan will be created.")
        return None
    print(f"✅ Selected file: {file_path}")
    return file_path

def launch_qgc():
    if not os.path.exists(QGC_PATH):
        print("❌ QGroundControl.AppImage not found at:", QGC_PATH)
        return

    try:
        print(" Launching QGroundControl...")
        subprocess.Popen([QGC_PATH])
        logger.log("Launched QGroundControl")
    except Exception as e:
        print("❌ Failed to launch QGC:", e)

def interpret_decision(nav: visionNav):
    if nav.mask_r is None or nav.mask_g is None or nav.middle_x is None:
        return "TURN_AROUND"
    middle_of_frame = nav.width // 2
    midpoint = nav.middle_x
    if abs(midpoint - middle_of_frame) < nav.width * 0.1:
        return "KEEP_ROUTE"
    elif midpoint < middle_of_frame:
        return "TURN_LEFT"
    else:
        return "TURN_RIGHT"

def handle_decision(decision, pwm: PWMController):
    logger.log(f" Decision: {decision}")

    if decision == "KEEP_ROUTE":
        pwm.go_forward()
    elif decision == "TURN_LEFT":
        pwm.steer_left()
    elif decision == "TURN_RIGHT":
        pwm.steer_right()
    elif decision == "TURN_AROUND":
        pwm.steer_left()
        time.sleep(1.5)
        pwm.steer_right()
        time.sleep(1.5)
    else:
        pwm.stop_all()

def main():
    print("🚤 NJORD Autonomous Boat Control - QGC Launch Mode")
    csv_path = ask_for_csv_path()
    if csv_path:
        convert_csv_to_plan(csv_path, PLAN_OUTPUT)
        logger.log(f"✅ CSV converted to {PLAN_OUTPUT}")
    else:
        logger.log("⚠️ No CSV path provided. Continuing without mission plan.")

    launch_qgc()  #  This is the part that launches QGC automatically

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("❌ Failed to open camera.")
        exit(1)

    nav = visionNav(video=cap)
    pwm = PWMController(MAVLINK_UDP)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            nav.image = frame
            nav.generate_masks()
            nav.detect_buoys()

            decision = interpret_decision(nav)
            handle_decision(decision, pwm)

            cv2.imshow("VisionNav Debug", nav.image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n🛑 Mission interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pwm.stop_all()
        logger.log(" Mission ended")
        logger.save_to_file(LOG_FILE_PATH)

if __name__ == "__main__":
    main()
