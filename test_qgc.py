from qgc_controller import QGCMissionController
import time

# Replace with correct connection string if needed
qgc = QGCMissionController(connection_str='/dev/ttyACM0')

qgc.pause_mission()
print("Mission Paused")
time.sleep(3)
qgc.resume_mission()
print("Mission Resumed")
