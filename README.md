# qgroundcontrol_py

Mission uploader and auto-loader for QGroundControl on Raspberry Pi 🛶  
Developed for Njord Challenge - IAAC Engineering Club

---

##  What This Tool Does

- Upload a `.csv` file of GPS waypoints (lat, lon)
- Converts it into a `.plan` file for QGroundControl
- Auto-saves the `.plan` to `qgc_autoload/AutoLoad.plan`
- Launches QGroundControl with software rendering
- Auto-loads the plan using `xdotool` (simulates Ctrl+L)
- Backs up each `.plan` to `qgc_plan_files/`

---

## 📂 Folder Structure

qgroundcontrol_py/
├── qgc_csv_uploader.py # PyQt5 GUI for mission upload
├── qgc_autoload/
│ └── launch_qgc.sh # xdotool trigger script
├── Sample_csv/ # Sample CSVs (optional)
├── qgc_plan_files/ # Saved .plan file backups
├── QGroundControl.AppImage # (Not pushed to GitHub - download manually from this link ) 
├── requirements.txt
└── README.md


---

##  Raspberry Pi Setup 

###  Step 1: Install Dependencies

```bash
sudo apt update
sudo apt install python3-pyqt5 xdotool

Download link:
👉 https://docs.qgroundcontrol.com/master/en/getting_started/download_and_install.html

Select:
QGroundControl for Linux → AppImage version

Then move the downloaded file to your project:
