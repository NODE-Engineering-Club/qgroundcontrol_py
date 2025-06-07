from vision import visionNav
from qgc_controller import QGCMissionController
from pwm_controller import PWMController
from mission_logger import MissionLogger

import cv2 as cv
import time

def main():
    logger = MissionLogger()
    qgc = QGCMissionController('/dev/ttyACM0')   # Change port if needed
    pwm = PWMController('/dev/ttyACM0')          # Same port for PWM commands
    
    # 🎥 CAMERA SETUP
    # For USB webcam (most common on Pi): use index 0 or 1
    # For Pi Camera Module: make sure it's enabled and use OpenCV with libcamera/GStreamer
    video = cv.VideoCapture(0)

    vision = visionNav(video=video)
    logger.log("✅ Main system started")

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        vision.image = frame
        vision.generate_masks()
        vision.detect_buoys()

        decision = ""  # Your vision-based maneuvering decision
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

        logger.log(f"📷 Vision: {decision}")

        if decision == "KEEP_ROUTE":
            pass  # QGC mission continues

        elif decision in ["TURN_LEFT", "TURN_RIGHT", "TURN_AROUND"]:
            qgc.pause_mission()
            logger.log("🛑 QGC mission paused")

            if decision == "TURN_LEFT":
                pwm.steer_left()
                logger.log("↩️ Steering LEFT")

            elif decision == "TURN_RIGHT":
                pwm.steer_right()
                logger.log("↪️ Steering RIGHT")

            elif decision == "TURN_AROUND":
                pwm.steer_left()
                pwm.steer_right()
                logger.log("🔁 Turn around sequence")

            time.sleep(2)
            pwm.stop_all()
            logger.log("⛔ Manual override stopped")

            qgc.resume_mission()
            logger.log("▶️ QGC mission resumed")

        cv.imshow("Live Vision", vision.image)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv.destroyAllWindows()
    logger.save_to_file("mission_log.txt")
    print("✅ Mission complete. Log saved.")

if __name__ == "__main__":
    main()
