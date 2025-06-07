import sys
import os
import csv
import json
import shutil
import subprocess
import cv2 as cv
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

        # Components for control
        self.qgc = QGCMissionController('/dev/ttyACM0')  # Update port as needed
        self.pwm = PWMController('/dev/ttyACM0')
        self.logger = MissionLogger()

    def select_csv(self):
        csv_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if not csv_path:
            return

        plan_save_path = os.path.join(os.getcwd(), "qgc_plan_files", "mission_auto.plan")
        try:
            self.convert_csv_to_plan(csv_path, plan_save_path)
            autoload_dir = os.path.expanduser("~/e_club/qgroundcontrol_py/qgc_autoload")
            os.makedirs(autoload_dir, exist_ok=True)
            shutil.copy(plan_save_path, os.path.join(autoload_dir, "AutoLoad.plan"))

            subprocess.Popen([
                "bash", "-c",
                f"cd ~/e_club/qgroundcontrol_py && ./QGroundControl.AppImage & sleep 5 && bash {autoload_dir}/launch_qgc.sh"
            ])

            QMessageBox.information(self, "Uploaded", "QGC Launched and Mission Auto-loaded. Starting control...")
            self.run_main_control()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

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

    def run_main_control(self):
        video = cv.VideoCapture(0)  # Change index if not detected
        nav = visionNav(video=video)

        try:
            while video.isOpened():
                ret, frame = video.read()
                if not ret:
                    break
                nav.image = frame
                nav.generate_masks()
                nav.detect_buoys()

                if nav.distance:
                    if "Turn Port" in nav.text_label or "left" in nav.text_label:
                        self.logger.log("Override: Port Turn")
                        self.qgc.pause_mission()
                        self.pwm.steer_left()
                    elif "Starboard" in nav.text_label or "right" in nav.text_label:
                        self.logger.log("Override: Starboard Turn")
                        self.qgc.pause_mission()
                        self.pwm.steer_right()
                    elif "Keep Route" in nav.text_label:
                        self.logger.log("Resume Mission")
                        self.qgc.resume_mission()

                cv.imshow("Boat Cam", nav.image)
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            video.release()
            cv.destroyAllWindows()
            self.logger.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QGCMissionApp()
    window.show()
    sys.exit(app.exec_())
