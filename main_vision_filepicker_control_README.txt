# ================================================
# 🚤 NJORD Autonomous Boat Controller - Instructions
# Filename: main_vision_filepicker.py
# System: Raspberry Pi (w/ camera + GUI support)
# ================================================

## 📦 Step 1: Install Required Packages
sudo apt update
sudo apt install python3-opencv python3-tk

## ✅ Optional: Test OpenCV Camera
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
# Output should be: True

## ⚙️ Step 2: Make QGroundControl AppImage Executable
cd /path/to/your/QGroundControl.AppImage
chmod +x QGroundControl.AppImage

## 🛠 Step 3: Check GUI Environment (for Tkinter + QGC)
# If you're running via SSH, make sure you use VNC or X11 forwarding
# Otherwise, run this directly from Pi desktop
# If needed:
export DISPLAY=:0

## 📁 Step 4: Run the Autonomous Boat Controller
# Make sure you are in the correct directory where main_vision_filepicker.py is saved
cd /path/to/your/script
python3 main_vision_filepicker.py

## 👇 What Happens Next:
# 1. A file picker window will appear → Select a GPS CSV file.
# 2. It will convert it into `mission.plan`.
# 3. You will be asked: "Launch QGroundControl? (y/n)"
#    → Press "y" to start QGC.
# 4. Vision system + PWM + mission control loop will begin.

## 🧠 Controls (Vision Based):
# - Keeps going if buoys are centered
# - Pauses and turns if buoys are off-center
# - Stops if no valid frame or buoy data

## 🛑 To stop:
- Press `Ctrl+C` in terminal
- Or press `q` in the OpenCV debug window

## 📄 Output Files:
- mission.plan       → Converted from your CSV
- mission_log.txt    → Mission log (decisions, events)

## ❗ Troubleshooting:
- If GUI doesn't appear, make sure you're running from Pi Desktop or using VNC.
- If camera doesn't work, test it with `raspistill` or USB cam on `/dev/video0`.
- If QGC doesn’t launch, try running it manually:
    ./QGroundControl.AppImage &
