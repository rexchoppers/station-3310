import base64
import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QMessageBox, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QDialog, QLineEdit
)

from PyQt6.QtCore import Qt

import crypt
from audio import generate_broadcast
from document import generate_spy_pad_pdf, preview_pdf_external
from missions import get_missions, add_mission, remove_mission
from decode import DecodeWindow

key = None

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

        # Show the encryption key dialog first
        if not self.show_key_dialog():
            # If the dialog was closed without a valid key, exit
            sys.exit(0)
            
        # Initialize the main UI
        self.init_ui()
        self.show()
    
    def show_key_dialog(self):
        """Show the encryption key dialog and return True if a valid key was provided"""
        # Create a custom dialog for encryption key input with Decode Only button
        key_dialog = QDialog(self)
        key_dialog.setWindowTitle("Encryption Key")
        key_dialog.setFixedSize(400, 150)
        
        dialog_layout = QVBoxLayout(key_dialog)
        
        # Add label and input field
        dialog_layout.addWidget(QLabel("Enter encryption key:"))
        key_input_field = QLineEdit()
        dialog_layout.addWidget(key_input_field)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(lambda: self.process_key_input(key_dialog, key_input_field))
        
        decode_button = QPushButton("Decode Only")
        decode_button.clicked.connect(lambda: self.open_decode_window(key_dialog))
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(key_dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(decode_button)
        button_layout.addWidget(cancel_button)
        
        dialog_layout.addLayout(button_layout)
        
        # Show the dialog and wait for user input
        result = key_dialog.exec()
        
        # Return True if the dialog was accepted (valid key provided)
        return result == QDialog.DialogCode.Accepted
    
    def process_key_input(self, dialog, key_input_field):
        """Process the encryption key input"""
        global key
        key_input = key_input_field.text()
        
        if not key_input:
            QMessageBox.critical(self, "Error", "Encryption key is required to use this application.")
            return
        
        # Convert the key to bytes for use with AESGCM
        try:
            key = base64.b64decode(key_input)
            dialog.accept()
        except:
            QMessageBox.critical(self, "Error", "Invalid encryption key format. Please provide a valid base64-encoded key.")
            return
    
    def open_decode_window(self, parent_dialog=None):
        decode_window = DecodeWindow(self)
        decode_window.exec()
        
        if parent_dialog:
            parent_dialog.reject()
            sys.exit(0)
    
    def init_ui(self):
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
        broadcast_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to align with data grid
        broadcast_layout.setSpacing(10)  # Add spacing between widgets
        broadcast_controls.setMaximumHeight(50)  # Limit the height of broadcast controls
        
        # Add text input field with validation
        self.broadcast_text = QTextEdit()
        self.broadcast_text.setFixedHeight(30)  # Make it a single line
        self.broadcast_text.setPlaceholderText("Enter broadcast message (max 25 chars)")
        self.broadcast_text.textChanged.connect(self.validate_broadcast_text)
        self.broadcast_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Expand horizontally
        
        # Add Generate button
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.on_generate_clicked)
        self.generate_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)  # Fixed size
        
        # Add widgets to layout
        broadcast_layout.addWidget(self.broadcast_text)
        broadcast_layout.addWidget(self.generate_button)
        
        # Add the broadcast controls to the content layout with no stretch
        self.content_layout.addWidget(broadcast_controls, 0)  # Set stretch factor to 0
        
        main_layout.addWidget(self.content_widget)
        
        # Populate mission list with mission IDs
        self.refresh_mission_list()

    def refresh_mission_list(self):
        self.mission_list.clear()
        self.missions = get_missions(key)

        for mission in self.missions:
            self.mission_list.addItem(mission.id)
            
        # Select the first mission if available
        if self.missions:
            self.mission_list.setCurrentRow(0)

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

            # Decrypt so we can reference the mission data
            mission.decrypt(key)

            # Refresh mission list
            self.refresh_mission_list()

            # Get pad lines (assuming mission.get_data() returns pad lines as list or multiline string)
            pad_data = mission.get_data()
            pad_lines = pad_data.splitlines()  # List of pad rows

            # Generate PDF bytes (make sure generate_spy_pad_pdf_bytes is imported)
            pdf_bytes = generate_spy_pad_pdf(pad_lines)
            preview_pdf_external(pdf_bytes)

            # Show success message
            QMessageBox.information(self, "Success", f"Mission '{mission.id}' added successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add mission: {str(e)}")
            
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
        message = self.broadcast_text.toPlainText().upper()
        
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
            f"The first row in the pad will be used and removed after generation. The broadcast generation may take a while to complete. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            encoded_message = "".join(crypt.LETTER_TO_DIGIT.get(ch, "00") for ch in message)

            pad_row = data[0].strip().replace(" ", "")

            ciphertext = crypt.otp_mod_encrypt(encoded_message, pad_row)
            # original_digits = crypt.otp_mod_decrypt(ciphertext, pad_row)

            generate_broadcast(self.current_mission.id, ciphertext)
            
            # Remove the first row from the pad data
            data = data[1:]  # Skip the first row
            updated_pad_data = "\n".join(data)
            
            # Update the mission data
            self.current_mission.update_data(updated_pad_data, key)

            self.update_mission_display()
            self.broadcast_text.clear()
            
            QMessageBox.information(self, "Success", "Broadcast generated successfully and pad row removed")
            
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
                mission_to_remove = None

                for mission in self.missions:
                    if mission.id == self.current_mission.id:
                        mission_to_remove = mission
                        break

                success = remove_mission(mission_to_remove)
                
                if success:
                    QMessageBox.information(self, "Success", f"Mission '{mission_to_remove.id}' removed successfully")
                    
                    self.current_mission = None
                    self.refresh_mission_list()
                    
                    self.mission_data.clear()
                    self.mission_data.setRowCount(0)
                    self.mission_data.setColumnCount(0)
                    
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