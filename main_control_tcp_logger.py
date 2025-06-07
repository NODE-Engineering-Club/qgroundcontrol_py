from vision import visionNav
from qgc_controller import QGCMissionController
from pwm_controller import PWMController
from mission_logger import MissionLogger

import cv2 as cv
import time
import socket
import logging

# === TCP LOGGER CONFIG ===
TCP_IP = '172.16.21.153'   # 🛠️ Replace with your laptop IP
TCP_PORT = 9999

# === SETUP LOCAL LOGGER ===
logging.basicConfig(filename="local_tcp_log.txt", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === ATTEMPT TCP CONNECTION ===
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_IP, TCP_PORT))
    logging.info("✅ TCP connection to base station established")
except Exception as e:
    logging.error(f"❌ TCP connection failed: {e}")
    sock = None

def send_log(message):
    logging.info(message)
    print(message)
    if sock:
        try:
            sock.sendall((message + '\n').encode())
        except Exception as e:
            logging.error(f"❌ TCP send failed: {e}")

def main():
    logger = MissionLogger()
    qgc = QGCMissionController('/dev/ttyACM0')
    pwm = PWMController('/dev/ttyACM0')

    video = cv.VideoCapture(0)
    vision = visionNav(video=video)

    send_log("🚀 [TCP LOGGER] Main system started")

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            send_log("⚠️ Frame read failed, exiting loop.")
            break

        vision.image = frame
        vision.generate_masks()
        vision.detect_buoys()

        decision = ""
        x_red = vision.middle_x
        x_green = vision.middle_x
        frame_center = vision.width // 2 if vision.width else 320

        if vision.mask_r is not None and vision.mask_g is not None:
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

        send_log(f"📷 Vision Decision: {decision}")
        logger.log(f"📷 Vision Decision: {decision}")

        if decision == "KEEP_ROUTE":
            pass

        elif decision in ["TURN_LEFT", "TURN_RIGHT", "TURN_AROUND"]:
            qgc.pause_mission()
            send_log("🛑 QGC mission paused")
            logger.log("🛑 QGC mission paused")

            if decision == "TURN_LEFT":
                pwm.steer_left()
                send_log("↩️ Steering LEFT")
            elif decision == "TURN_RIGHT":
                pwm.steer_right()
                send_log("↪️ Steering RIGHT")
            elif decision == "TURN_AROUND":
                pwm.steer_left()
                pwm.steer_right()
                send_log("🔁 Turn around")

            time.sleep(2)
            pwm.stop_all()
            send_log("⛔ Manual override stopped")

            qgc.resume_mission()
            send_log("▶️ QGC mission resumed")

        cv.imshow("Live Vision", vision.image)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv.destroyAllWindows()
    logger.save_to_file("mission_log.txt")
    send_log("✅ Mission complete. Logs saved.")

    if sock:
        sock.close()

if __name__ == "__main__":
    main()
