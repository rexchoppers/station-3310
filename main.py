import base64
import json
import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt

from missions import get_missions, add_mission

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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
        
        # Add mission data as a table
        self.mission_data = QTableWidget()
        self.mission_data.setColumnCount(0)
        self.mission_data.setRowCount(0)
        self.mission_data.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.content_layout.addWidget(self.mission_data)

        main_layout.addWidget(self.content_widget)
        
        # Populate mission list with mission IDs
        self.refresh_mission_list()

        self.show()





    def refresh_mission_list(self):
        self.mission_list.clear()
        self.missions = get_missions()

        for mission in self.missions:
            self.mission_list.addItem(mission.id)
            print(mission.data)
    
    def on_mission_selected(self, index):
        """Handle mission selection from the list"""
        if index < 0 or index >= len(self.missions):
            return
            
        self.current_mission = self.missions[index]
        self.update_mission_display()
    
    def update_mission_display(self):
        self.mission_data.clear()
        self.mission_data.setRowCount(0)
        self.mission_data.setColumnCount(0)
        
        if not self.current_mission:
            return
            
        # Check if mission is decrypted
        if self.current_mission.is_decrypted():
            mission_data = self.current_mission.get_data()
            data_list = json.loads(mission_data)
            
            if not data_list:
                return
                
            # Determine the structure of the data and set up the table accordingly
            if isinstance(data_list[0], dict):
                # Dictionary items - use keys as column headers
                headers = list(data_list[0].keys())
                self.mission_data.setColumnCount(len(headers))
                self.mission_data.setHorizontalHeaderLabels(headers)
                
                # Add rows
                for row_idx, item in enumerate(data_list):
                    self.mission_data.insertRow(row_idx)
                    for col_idx, key in enumerate(headers):
                        value = item.get(key, "")
                        table_item = QTableWidgetItem(str(value))
                        table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        self.mission_data.setItem(row_idx, col_idx, table_item)
                        
            elif isinstance(data_list[0], list):
                # List items - use numeric column headers
                max_cols = max(len(item) for item in data_list)
                self.mission_data.setColumnCount(max_cols)
                self.mission_data.setHorizontalHeaderLabels([str(i+1) for i in range(max_cols)])
                
                # Add rows
                for row_idx, item in enumerate(data_list):
                    self.mission_data.insertRow(row_idx)
                    for col_idx, value in enumerate(item):
                        self.mission_data.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            else:
                # Primitive items - use a single column
                self.mission_data.setColumnCount(1)
                self.mission_data.setHorizontalHeaderLabels(["Data"])
                
                # Add rows
                for row_idx, item in enumerate(data_list):
                    self.mission_data.insertRow(row_idx)
                    self.mission_data.setItem(row_idx, 0, QTableWidgetItem(str(item)))
                    
            # Resize columns to content
            self.mission_data.resizeColumnsToContents()


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