sudo apt update
sudo apt install python3-venv python3-pip -y

python3 -m venv venv
source venv/bin/activate

3. Install Required Python Packages

pip install --upgrade pip
pip install -r requirements.txt

if you get errors
pip install --break-system-packages -r requirements.txt

pyQT5 error hits
sudo apt install python3-pyqt5 -y

install open CV dependancies
sudo apt install libopencv-dev python3-opencv -y

permission to pixhawk
sudo usermod -a -G dialout $USER

sudo reboot
cd ~/qgroundcontrol_py
source venv/bin/activate
python3 main_controller.py


