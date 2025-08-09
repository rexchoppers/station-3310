import sys
import secrets

from PyQt6.QtWidgets import QApplication, QMainWindow

from crypt import generate_mission_id


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialise basic parameters
        self.setWindowTitle("Station 3310")
        self.setGeometry(100, 100, 800, 600)

        # Disable resizing
        self.setFixedSize(800, 600)

        self.show()

        # Generate a random mission ID



app = QApplication(sys.argv)
w = MainWindow()
app.exec()