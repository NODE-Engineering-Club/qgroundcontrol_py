import os
import time
import cv2
import tkinter as tk
from tkinter import filedialog

from vision import visionNav
from qgc_controller import pause_mission, resume_mission
from pwm_controller import PWMController
from qgc_plan_converter import convert_csv_to_plan
from mission_logger import MissionLogger

# === CONFIG ===
CAMERA_INDEX = 0
SERIAL_PORT = "/dev/ttyACM0"
PLAN_OUTPUT = "mission.plan"
LOG_FILE_PATH = "mission_log.txt"

logger = MissionLogger()

def ask_for_csv_path():
    root = tk.Tk()
    root.withdraw()  # Hide root window

    file_path = filedialog.askopenfilename(
        title="Select GPS CSV File",
        filetypes=[("CSV Files", "*.csv")]
    )

    if not file_path:
        print("❌ No file selected. Exiting.")
        exit(1)

    print(f"✅ Selected file: {file_path}")
    return file_path

def launch_qgc():
    if input("Launch QGroundControl? (y/n): ").lower().startswith("y"):
        os.system("./QGroundControl.AppImage &")
        logger.log("Launched QGroundControl")

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
        pause_mission(SERIAL_PORT)
        pwm.steer_left()
        resume_mission(SERIAL_PORT)
    elif decision == "TURN_RIGHT":
        pause_mission(SERIAL_PORT)
        pwm.steer_right()
        resume_mission(SERIAL_PORT)
    elif decision == "TURN_AROUND":
        pause_mission(SERIAL_PORT)
        pwm.steer_left()
        time.sleep(1.5)
        pwm.steer_right()
        time.sleep(1.5)
        resume_mission(SERIAL_PORT)
    else:
        pwm.stop_all()

def main():
    print("NJORD Autonomous Boat Control v1.0")

    csv_path = ask_for_csv_path()
    convert_csv_to_plan(csv_path, PLAN_OUTPUT)
    logger.log(f"✅ CSV converted to {PLAN_OUTPUT}")

    launch_qgc()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("❌ Failed to open webcam.")
        exit(1)

    nav = visionNav(video=cap)
    pwm = PWMController(SERIAL_PORT)

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
