from PyQt5.QtWidgets import QApplication, QWidget
import sys

print("Starting PyQt test")

app = QApplication(sys.argv)
w = QWidget()
w.setWindowTitle("Test Window")
w.show()

print("Showing window")
sys.exit(app.exec_())
