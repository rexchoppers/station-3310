import sys
import os
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox
)

import crypt
from missions import get_missions
from crypt import generate_mission_id

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialise basic parameters
        self.setWindowTitle("Station 3310")
        self.setGeometry(100, 100, 800, 600)

        # Disable resizing
        self.setFixedSize(800, 600)

        # On the left hand side, add missions selection
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create left side panel with mission list and add button
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(200)  # Set width for the left panel
        
        # Create mission list widget
        self.mission_list = QListWidget()
        left_layout.addWidget(self.mission_list)
        
        # Add "Add Mission" button
        add_mission_button = QPushButton("Add Mission")
        add_mission_button.clicked.connect(self.add_mission)
        left_layout.addWidget(add_mission_button)
        
        main_layout.addWidget(left_panel)
        
        # Create content area (right side)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        main_layout.addWidget(content_widget)
        
        # Populate mission list with mission IDs
        self.refresh_mission_list()

        self.show()
        
    def refresh_mission_list(self):
        """Refresh the mission list with the latest missions"""
        self.mission_list.clear()
        missions = get_missions()
        for mission in missions:
            self.mission_list.addItem(mission["name"])
            
    def add_mission(self):
        mission_id = generate_mission_id()
        
        # Create mission directory
        current_dir = Path(__file__).parent

        try:


            print(crypt.generate_pad())
            
            # with open(mission_dir / "mission.json", 'w', encoding='utf-8') as f:
              #  json.dump(mission_data, f, indent=4)
                
            # self.refresh_mission_list()

            # QMessageBox.information(
             #    self, "Success", f"Mission '{mission_name}' added successfully!"
            # )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to add mission: {str(e)}"
            )

app = QApplication(sys.argv)
w = MainWindow()
app.exec()