import base64
import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)

from PyQt6.QtCore import Qt
from pydub import AudioSegment

from audio import append_mission_id_segment
from missions import get_missions, add_mission, remove_mission
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Encryption key for mission data (256-bit key)
# This will be set by user input
key = None

# Letter to two-digit number (A=01 to Z=26, space=00)
LETTER_TO_DIGIT = {chr(i + 65): f"{i + 1:02d}" for i in range(26)}
LETTER_TO_DIGIT[' '] = "00"

# Test example
# text = "MEET AT DAWN"
# encoded = ''.join(LETTER_TO_DIGIT[ch] for ch in text)
# print("Encoded:", encoded)

def generate_broadcast():
    example_mission_id = "F1YNE"

    broadcast_audio = (
        AudioSegment.from_mp3("resources/jingle.mp3") +
        AudioSegment.silent(duration=2000) +
        AudioSegment.from_mp3("resources/jingle.mp3") +
        AudioSegment.silent(duration=2000) +
        AudioSegment.from_mp3("resources/jingle.mp3") +
        AudioSegment.silent(duration=2000)
    )


    # Add the mission ID to the audio + repeat 5 times
    for _ in range(5):
        broadcast_audio = append_mission_id_segment(broadcast_audio, example_mission_id)
        broadcast_audio += AudioSegment.silent(duration=1000)

    # Add howler for message segment
    broadcast_audio += AudioSegment.silent(duration=1000)
    broadcast_audio += AudioSegment.from_mp3("resources/howler.mp3")[:10000]

    broadcast_audio.export("broadcast.mp3", format="mp3")
    print("Broadcast saved as broadcast.mp3")

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

        generate_broadcast()

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
        
        # Add "Remove Mission" button
        self.remove_mission_button = QPushButton("Remove Mission")
        self.remove_mission_button.clicked.connect(self.remove_mission)
        self.remove_mission_button.setEnabled(False)  # Disable until a mission is selected
        left_layout.addWidget(self.remove_mission_button)
        
        main_layout.addWidget(left_panel)
        
        # Create content area (right side)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # Add mission data as a table
        self.mission_data = QTableWidget()
        self.mission_data.setColumnCount(0)
        self.mission_data.setRowCount(0)
        self.mission_data.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Make the data table take up more vertical space
        self.content_layout.addWidget(self.mission_data, 1)  # Set stretch factor to 1
        
        # Add a horizontal layout for the broadcast controls underneath the data table
        broadcast_controls = QWidget()
        broadcast_layout = QHBoxLayout(broadcast_controls)
        broadcast_controls.setMaximumHeight(50)  # Limit the height of broadcast controls

        # Add text input field with validation
        self.broadcast_text = QTextEdit()
        self.broadcast_text.setFixedHeight(30)  # Make it a single line
        self.broadcast_text.setPlaceholderText("Enter broadcast message (max 25 chars)")
        self.broadcast_text.textChanged.connect(self.validate_broadcast_text)

        # Add Generate button
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.on_generate_clicked)

        # Add widgets to layout
        broadcast_layout.addWidget(self.broadcast_text)
        broadcast_layout.addWidget(self.generate_button)

        # Add the broadcast controls to the content layout with no stretch
        self.content_layout.addWidget(broadcast_controls, 0)  # Set stretch factor to 0

        main_layout.addWidget(self.content_widget)
        
        # Populate mission list with mission IDs
        self.refresh_mission_list()

        self.show()

    def refresh_mission_list(self):
        self.mission_list.clear()
        self.missions = get_missions(key)

        print("Refresh called")

        for mission in self.missions:
            self.mission_list.addItem(mission.id)

    def on_mission_selected(self, index):
        """Handle mission selection from the list"""
        if index < 0 or index >= len(self.missions):
            self.remove_mission_button.setEnabled(False)
            return
            
        self.current_mission = self.missions[index]
        self.remove_mission_button.setEnabled(True)
        self.update_mission_display()
    
    def update_mission_display(self):
        self.mission_data.clear()
        self.mission_data.setRowCount(0)
        self.mission_data.setColumnCount(0)
        
        if not self.current_mission:
            return
            
        # Check if mission is decrypted
        if self.current_mission.is_decrypted():
            data = self.current_mission.get_data()

            self.mission_data.setColumnCount(1)
            self.mission_data.setHorizontalHeaderLabels(["Data"])

            data = data.splitlines()

            # Add rows
            for row_idx, item in enumerate(data):
                self.mission_data.insertRow(row_idx)
                table_item = QTableWidgetItem(str(item))
                table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mission_data.setItem(row_idx, 0, table_item)

            self.mission_data.resizeColumnsToContents()


    def add_mission(self):
        try:
            mission = add_mission(key)
            # mission.decrypt(key)
            
            # QMessageBox.information(self, "Success", f"Mission '{mission.id}' added successfully")
            
            # Refresh the mission list
            self.refresh_mission_list()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to add mission: {str(e)}"
            )
            
    def validate_broadcast_text(self):
        """Validate the broadcast text input"""
        text = self.broadcast_text.toPlainText()
        
        # Remove any punctuation or invalid characters
        valid_text = ''.join(ch for ch in text if ch.isalpha() or ch.isspace())
        
        # Truncate to 25 characters
        if len(valid_text) > 25:
            valid_text = valid_text[:25]
        
        # Update the text if it changed
        if valid_text != text:
            self.broadcast_text.setPlainText(valid_text)
            # Move cursor to the end
            cursor = self.broadcast_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.broadcast_text.setTextCursor(cursor)
            
    def on_generate_clicked(self):
        """Handle Generate button click"""
        # Check if there's a selected mission with data
        if not self.current_mission or not self.current_mission.is_decrypted():
            QMessageBox.warning(self, "Warning", "Please select a decrypted mission first")
            return
            
        # Get the message text
        message = self.broadcast_text.toPlainText().strip().upper()
        
        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a message to broadcast")
            return
        
        # Check if there's at least one row in the pad
        data = self.current_mission.get_data().splitlines()
        if not data:
            QMessageBox.warning(self, "Warning", "The selected mission has no one-time pad data")
            return
        
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Broadcast Generation",
            f"The first row in the pad will be used and removed after generation. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Call the generate_broadcast function
            generate_broadcast()
            
            QMessageBox.information(self, "Success", "Broadcast generated successfully")
            
    def remove_mission(self):
        if not self.current_mission:
            return
            
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove mission '{self.current_mission.id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Get mission from `missions` list
                mission_to_remove = None

                for mission in self.missions:
                    if mission.id == self.current_mission.id:
                        mission_to_remove = mission
                        break

                success = remove_mission(mission_to_remove)
                
                if success:
                    QMessageBox.information(self, "Success", f"Mission '{mission_to_remove.id}' removed successfully")
                    
                    # Clear current mission
                    self.current_mission = None
                    
                    # Refresh the mission list
                    self.refresh_mission_list()
                    
                    # Clear the mission display
                    self.mission_data.clear()
                    self.mission_data.setRowCount(0)
                    self.mission_data.setColumnCount(0)
                    
                    # Disable the remove button
                    self.remove_mission_button.setEnabled(False)
                else:
                    QMessageBox.warning(self, "Warning", f"Could not find mission file to remove")
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to remove mission: {str(e)}"
                )

app = QApplication(sys.argv)
w = MainWindow()
app.exec()