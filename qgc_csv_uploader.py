import sys
import csv
import json
import subprocess
import os
import shutil
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox
)

class QGCMissionUploader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QGC Mission Uploader")
        self.setFixedSize(400, 220)

        layout = QVBoxLayout()
        self.upload_button = QPushButton("Upload CSV File & Launch QGC")
        self.upload_button.clicked.connect(self.select_csv)
        layout.addWidget(self.upload_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_csv(self):
        csv_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if not csv_path:
            self.launch_qgc_only()
            return

        plan_save_path, _ = QFileDialog.getSaveFileName(
            self, "Save .plan File", "mission.plan", "Plan Files (*.plan)"
        )
        if not plan_save_path:
            return

        try:
            self.convert_csv_to_plan(csv_path, plan_save_path)

            # Copy to autoload path
            autoload_path = os.path.expanduser("~/e_club/qgroundcontrol_py/qgc_autoload/AutoLoad.plan")
            os.makedirs(os.path.dirname(autoload_path), exist_ok=True)
            shutil.copy(plan_save_path, autoload_path)

            # Backup to qgc_plan_files with timestamp
            backup_dir = os.path.expanduser("~/e_club/qgroundcontrol_py/qgc_plan_files")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"mission_{timestamp}.plan")
            shutil.copy(plan_save_path, backup_path)

            # Clean .Zone.Identifier file if created
            zone_id_file = plan_save_path + ":Zone.Identifier"
            if os.path.exists(zone_id_file):
                os.remove(zone_id_file)

            self.launch_qgc_only()
            QMessageBox.information(self, "Success", "QGC launched and mission loading triggered.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load mission:\n{str(e)}")

    def launch_qgc_only(self):
        appimage_path = os.path.expanduser("~/e_club/qgroundcontrol_py/QGroundControl.AppImage")
        launch_script_path = os.path.expanduser("~/e_club/qgroundcontrol_py/qgc_autoload/launch_qgc.sh")

        subprocess.Popen([
            "bash", "-c",
            f"LIBGL_ALWAYS_SOFTWARE=1 {appimage_path} & sleep 5 && bash {launch_script_path}"
        ])

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QGCMissionUploader()
    window.show()
    sys.exit(app.exec_())
