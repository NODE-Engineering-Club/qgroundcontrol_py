import os
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/usr/lib/x86_64-linux-gnu/qt5/plugins/platforms"
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import sys
import os
import csv
import json
import shutil
import subprocess
import cv2 as cv
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox
)

from vision import visionNav
from qgc_controller import QGCMissionController
from pwm_controller import PWMController
from mission_logger import MissionLogger

class QGCMissionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QGC Mission + Vision Control")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        self.upload_button = QPushButton("Upload CSV & Start Mission")
        self.upload_button.clicked.connect(self.select_csv)
        layout.addWidget(self.upload_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Initialize control attributes but DO NOT connect yet
        self.qgc = None
        self.pwm = None
        self.logger = None
        self.vision = None
        self.video = None

    def select_csv(self):
        csv_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if not csv_path:
            return

        # Prepare paths
        plan_dir = os.path.join(os.getcwd(), "qgc_plan_files")
        os.makedirs(plan_dir, exist_ok=True)
        plan_save_path = os.path.join(plan_dir, "mission_auto.plan")

        try:
            self.convert_csv_to_plan(csv_path, plan_save_path)

            autoload_dir = os.path.expanduser("~/e_club/qgroundcontrol_py/qgc_autoload")
            os.makedirs(autoload_dir, exist_ok=True)
            shutil.copy(plan_save_path, os.path.join(autoload_dir, "AutoLoad.plan"))

            # Launch QGroundControl asynchronously
            subprocess.Popen([
                "bash", "-c",
                f"cd ~/e_club/qgroundcontrol_py && ./QGroundControl.AppImage & sleep 5 && bash {autoload_dir}/launch_qgc.sh"
            ])

            QMessageBox.information(self, "Success", "QGC Launched and Mission Auto-loaded.\nStarting vision control...")

            # Now initialize Pixhawk and vision after GUI response
            self.start_mission_control()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {str(e)}")

    def convert_csv_to_plan(self, csv_file, plan_path, default_alt=2.0):
        waypoints = []
        with open(csv_file, newline='') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                lat = float(row.get('latitude') or row.get('Latitude'))
                lon = float(row.get('longitude') or row.get('Longitude'))
                waypoints.append({
                    "AMSLAltAboveTerrain": None,
                    "Altitude": default_alt,
                    "AltitudeMode": 1,
                    "autoContinue": True,
                    "command": 16,
                    "doJumpId": i + 1,
                    "frame": 3,
                    "params": [0, 0, 0, None, lat, lon, default_alt],
                    "type": "SimpleItem"
                })

        plan = {
            "fileType": "Plan",
            "groundStation": "QGroundControl",
            "version": 1,
            "geoFence": {"circles": [], "polygons": [], "version": 2},
            "rallyPoints": {"points": [], "version": 2},
            "mission": {
                "cruiseSpeed": 1.5,
                "firmwareType": 3,
                "hoverSpeed": 3,
                "items": waypoints,
                "plannedHomePosition": [
                    waypoints[0]["params"][4],
                    waypoints[0]["params"][5],
                    waypoints[0]["params"][6]
                ],
                "vehicleType": 2,
                "version": 2
            }
        }

        with open(plan_path, "w") as f:
            json.dump(plan, f, indent=4)

    def start_mission_control(self):
        try:
            self.qgc = QGCMissionController('/dev/ttyACM0')  # Change port if needed
            self.pwm = PWMController('/dev/ttyACM0')
            self.logger = MissionLogger()
            self.video = cv.VideoCapture(0)  # Change if webcam index differs
            self.vision = visionNav(video=self.video)
            self.logger.log("Mission control started.")

            # Run vision loop in a separate thread to keep GUI responsive
            vision_thread = threading.Thread(target=self.run_vision_loop, daemon=True)
            vision_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start mission control: {str(e)}")

    def run_vision_loop(self):
        while self.video.isOpened():
            ret, frame = self.video.read()
            if not ret:
                break

            self.vision.image = frame
            self.vision.generate_masks()
            self.vision.detect_buoys()

            decision = ""
            x_red = self.vision.middle_x or 0
            x_green = self.vision.middle_x or 0
            frame_center = self.vision.width // 2 if self.vision.width else 320

            if self.vision.mask_r is not None and self.vision.mask_g is not None:
                if abs(x_red - frame_center) < 50 and abs(x_green - frame_center) < 50:
                    decision = "KEEP_ROUTE"
                elif x_red > x_green:
                    decision = "TURN_LEFT"
                elif x_green > x_red:
                    decision = "TURN_RIGHT"
                else:
                    decision = "TURN_AROUND"
            else:
                decision = "KEEP_ROUTE"

            self.logger.log(f"Vision decision: {decision}")

            if decision == "KEEP_ROUTE":
                pass  # Let QGC continue

            elif decision in ["TURN_LEFT", "TURN_RIGHT", "TURN_AROUND"]:
                self.qgc.pause_mission()
                self.logger.log("QGC mission paused.")

                if decision == "TURN_LEFT":
                    self.pwm.steer_left()
                    self.logger.log("Steering LEFT.")

                elif decision == "TURN_RIGHT":
                    self.pwm.steer_right()
                    self.logger.log("Steering RIGHT.")

                elif decision == "TURN_AROUND":
                    self.pwm.steer_left()
                    self.pwm.steer_right()
                    self.logger.log("Performing TURN_AROUND sequence.")

                cv.waitKey(2000)  # Wait 2 seconds for maneuver
                self.pwm.stop_all()
                self.logger.log("Stopped manual override.")

                self.qgc.resume_mission()
                self.logger.log("QGC mission resumed.")

            cv.imshow("Boat Vision", self.vision.image)
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

        self.video.release()
        cv.destroyAllWindows()
        self.logger.save_to_file("mission_log.txt")
        self.logger.log("Mission ended.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QGCMissionApp()
    window.show()
    sys.exit(app.exec_())
