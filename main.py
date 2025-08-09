import base64
import sys
import os
import json

from pathlib import Path
from dotenv import load_dotenv

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QLabel, QTextEdit
)

import crypt
from missions import get_missions, Mission, add_mission
from crypt import generate_mission_id

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()

# Encryption key for mission data (256-bit key)
# This will be set by user input
key = None

def generate_and_save_key(filepath: str):
    key = AESGCM.generate_key(bit_length=256)  # bytes
    # Encode to base64 string
    b64_key = base64.b64encode(key).decode('utf-8')
    # Save to file
    with open(filepath, 'w') as f:
        f.write(b64_key)
    print(f"Key saved to {filepath}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialise basic parameters
        self.setWindowTitle("Station 3310")
        self.setGeometry(100, 100, 800, 600)

        # Disable resizing
        self.setFixedSize(800, 600)

        # Store loaded missions
        self.missions = []
        self.current_mission = None

        # generate_and_save_key("key.txt")

        # Prompt the user input for the encryption key
        global key
        key_input, ok = QInputDialog.getText(self, "Encryption Key", "Enter encryption key:")
        if not ok or not key_input:
            QMessageBox.critical(self, "Error", "Encryption key is required to use this application.")
            sys.exit(1)
        
        # Convert the key to bytes for use with AESGCM
        try:
            key = base64.b64decode(key_input)
        except:
            QMessageBox.critical(self, "Error", "Invalid encryption key format. Please provide a valid base64-encoded key.")
            sys.exit(1)


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
        self.mission_list.currentRowChanged.connect(self.on_mission_selected)
        left_layout.addWidget(self.mission_list)
        
        # Add "Add Mission" button
        add_mission_button = QPushButton("Add Mission")
        add_mission_button.clicked.connect(self.add_mission)
        left_layout.addWidget(add_mission_button)
        
        main_layout.addWidget(left_panel)
        
        # Create content area (right side)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # Add mission title label
        self.mission_title = QLabel("Select a mission")
        self.mission_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.content_layout.addWidget(self.mission_title)
        
        # Add mission description
        self.mission_description = QTextEdit()
        self.mission_description.setReadOnly(True)
        self.content_layout.addWidget(self.mission_description)
        
        # Add mission steps
        self.mission_steps = QTextEdit()
        self.mission_steps.setReadOnly(True)
        self.content_layout.addWidget(self.mission_steps)
        
        # Add decrypt button
        self.decrypt_button = QPushButton("Decrypt Mission")
        self.decrypt_button.setVisible(False)
        self.content_layout.addWidget(self.decrypt_button)

        main_layout.addWidget(self.content_widget)
        
        # Populate mission list with mission IDs
        self.refresh_mission_list()

        self.show()





    def refresh_mission_list(self):
        self.mission_list.clear()
        self.missions = get_missions()

        for mission in self.missions:
            item_text = mission.id
            if not mission.is_decrypted():
                item_text += " [ENCRYPTED]"
            self.mission_list.addItem(item_text)
    
    def on_mission_selected(self, index):
        """Handle mission selection from the list"""
        if index < 0 or index >= len(self.missions):
            return
            
        self.current_mission = self.missions[index]
        self.update_mission_display()
    
    def update_mission_display(self):
        """Update the mission display area with the current mission data"""
        if not self.current_mission:
            self.mission_title.setText("Select a mission")
            self.mission_description.setText("")
            self.mission_steps.setText("")
            self.decrypt_button.setVisible(False)
            return
            
        # Update mission title
        self.mission_title.setText(f"Mission: {self.current_mission.id}")
        
        # Check if mission is decrypted
        if self.current_mission.is_decrypted():
            mission_data = self.current_mission.get_data()
            
            self.decrypt_button.setVisible(False)
        else:
            # Show encrypted message and decrypt button
            self.mission_description.setText("This mission is encrypted.")
            self.mission_steps.setText("Decrypt the mission to view its contents.")
            self.decrypt_button.setVisible(True)

            
    def add_mission(self):
        try:
            mission = add_mission(key)
            
            # Add the new mission to our list
            self.missions.append(mission)
            
            QMessageBox.information(self, "Success", f"Mission '{mission.id}' added successfully")
            
            # Refresh the mission list
            self.refresh_mission_list()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to add mission: {str(e)}"
            )

app = QApplication(sys.argv)
w = MainWindow()
app.exec()