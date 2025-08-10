"""
Station 3310 - Main Application

This module provides the main GUI application for Station 3310, a tool for managing
encrypted missions, generating broadcasts, and decoding messages.
"""

import base64
import logging
import sys
from typing import List, Optional, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QMessageBox, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QDialog, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor

import crypt
from audio import generate_broadcast
from document import generate_spy_pad_pdf, preview_pdf_external
from missions import Mission, get_missions, add_mission, remove_mission
from decode import DecodeWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MainWindow(QMainWindow):
    """
    Main application window for Station 3310.
    
    This class handles the main UI, mission management, and broadcast generation.
    """
    
    def __init__(self) -> None:
        """Initialize the main window and its components."""
        super().__init__()

        # Initialize encryption key
        self.encryption_key: Optional[bytes] = None
        
        # Initialize basic parameters
        self.setWindowTitle("Station 3310")
        self.setGeometry(100, 100, 800, 600)

        # Disable resizing
        self.setFixedSize(800, 600)

        # Store loaded missions
        self.missions: List[Mission] = []
        self.current_mission: Optional[Mission] = None

        # Show the encryption key dialog first
        if not self.show_key_dialog():
            # If the dialog was closed without a valid key, exit
            logging.info("Application exiting: No valid encryption key provided")
            sys.exit(0)
            
        # Initialize the main UI
        self.init_ui()
        self.show()
    
    def show_key_dialog(self) -> bool:
        """
        Show the encryption key dialog and process user input.
        
        Returns:
            bool: True if a valid key was provided, False otherwise
        """
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
    
    def process_key_input(self, dialog: QDialog, key_input_field: QLineEdit) -> None:
        """
        Process the encryption key input from the dialog.
        
        Args:
            dialog: The dialog containing the key input field
            key_input_field: The QLineEdit containing the key input
        """
        key_input = key_input_field.text()
        
        if not key_input:
            QMessageBox.critical(self, "Error", "Encryption key is required to use this application.")
            return
        
        # Convert the key to bytes for use with AESGCM
        try:
            self.encryption_key = base64.b64decode(key_input)
            dialog.accept()
            logging.info("Valid encryption key provided")
        except base64.binascii.Error:
            QMessageBox.critical(self, "Error", "Invalid encryption key format. Please provide a valid base64-encoded key.")
            logging.warning("Invalid encryption key format provided")
    
    def open_decode_window(self, parent_dialog: Optional[QDialog] = None) -> None:
        """
        Open the decode window for decoding messages without using the main application.
        
        Args:
            parent_dialog: Optional parent dialog that will be closed if provided
        """
        decode_window = DecodeWindow(self)
        decode_window.exec()
        
        if parent_dialog:
            parent_dialog.reject()
            logging.info("Exiting application after using decode-only mode")
            sys.exit(0)
    
    def init_ui(self) -> None:
        """
        Initialize the user interface components.
        
        This method sets up the main window layout, including the mission list,
        mission data display, and broadcast controls.
        """
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create left side panel
        self._setup_left_panel(main_layout)
        
        # Create right side content area
        self._setup_content_area(main_layout)
        
        # Populate mission list with mission IDs
        self.refresh_mission_list()
        
    def _setup_left_panel(self, main_layout: QHBoxLayout) -> None:
        """
        Set up the left panel with mission list and control buttons.
        
        Args:
            main_layout: The main layout to add the left panel to
        """
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
        
    def _setup_content_area(self, main_layout: QHBoxLayout) -> None:
        """
        Set up the right side content area with mission data and broadcast controls.
        
        Args:
            main_layout: The main layout to add the content area to
        """
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
        
        # Add broadcast controls
        self._setup_broadcast_controls()
        
        main_layout.addWidget(self.content_widget)
        
    def _setup_broadcast_controls(self) -> None:
        """Set up the broadcast controls for message input and generation."""
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

    def refresh_mission_list(self) -> None:
        """
        Refresh the mission list with the latest missions from storage.
        
        This method clears the current mission list, loads missions using the encryption key,
        and selects the first mission if available.
        """
        self.mission_list.clear()
        
        if self.encryption_key is None:
            logging.error("Cannot refresh mission list: No encryption key available")
            return
            
        self.missions = get_missions(self.encryption_key)
        logging.info(f"Loaded {len(self.missions)} missions")

        for mission in self.missions:
            self.mission_list.addItem(mission.id)
            
        # Select the first mission if available
        if self.missions:
            self.mission_list.setCurrentRow(0)

    def on_mission_selected(self, index: int) -> None:
        """
        Handle mission selection from the list.
        
        Args:
            index: The index of the selected mission in the list
        """
        if index < 0 or index >= len(self.missions):
            self.remove_mission_button.setEnabled(False)
            return
            
        self.current_mission = self.missions[index]
        self.remove_mission_button.setEnabled(True)
        logging.info(f"Selected mission: {self.current_mission.id}")
        self.update_mission_display()
    
    def update_mission_display(self) -> None:
        """
        Update the mission data display with the current mission's data.
        
        This method clears the current display and populates it with the
        data from the currently selected mission, if available.
        """
        # Clear the current display
        self.mission_data.clear()
        self.mission_data.setRowCount(0)
        self.mission_data.setColumnCount(0)
        
        if not self.current_mission:
            logging.debug("No mission selected, display cleared")
            return
            
        # Check if mission is decrypted
        if self.current_mission.is_decrypted():
            data = self.current_mission.get_data()
            data_lines = data.splitlines()
            
            logging.debug(f"Displaying {len(data_lines)} lines of mission data")

            # Set up the table
            self.mission_data.setColumnCount(1)
            self.mission_data.setHorizontalHeaderLabels(["Data"])

            # Add rows
            for row_idx, item in enumerate(data_lines):
                self.mission_data.insertRow(row_idx)
                table_item = QTableWidgetItem(str(item))
                # Make the item non-editable
                table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mission_data.setItem(row_idx, 0, table_item)

            self.mission_data.resizeColumnsToContents()
        else:
            logging.warning(f"Mission {self.current_mission.id} is not decrypted, cannot display data")

    def add_mission(self) -> None:
        """
        Add a new mission with a generated one-time pad.
        
        This method creates a new mission with a randomly generated one-time pad,
        displays the pad as a PDF, and adds the mission to the list.
        """
        if self.encryption_key is None:
            logging.error("Cannot add mission: No encryption key available")
            QMessageBox.critical(self, "Error", "Encryption key is required to add a mission")
            return
            
        try:
            # Create a new mission with a generated one-time pad
            mission = add_mission(self.encryption_key)
            logging.info(f"Created new mission with ID: {mission.id}")

            # Decrypt so we can reference the mission data
            mission.decrypt(self.encryption_key)

            # Refresh mission list
            self.refresh_mission_list()

            # Get pad lines from the mission data
            pad_data = mission.get_data()
            pad_lines = pad_data.splitlines()

            # Generate PDF and preview it
            pdf_bytes = generate_spy_pad_pdf(pad_lines)
            preview_pdf_external(pdf_bytes)
            logging.info("Generated and displayed one-time pad PDF")

            # Show success message
            QMessageBox.information(self, "Success", f"Mission '{mission.id}' added successfully")
        except Exception as e:
            error_msg = f"Failed to add mission: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
            
    def validate_broadcast_text(self) -> None:
        """
        Validate and sanitize the broadcast text input.
        
        This method ensures that the broadcast text contains only letters and spaces,
        and is limited to 25 characters.
        """
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

    def _encode_message(self, message: str) -> str:
        """
        Encode a message using the letter-to-digit mapping.
        
        Args:
            message: The message to encode (uppercase letters and spaces)
            
        Returns:
            The encoded message as a string of digits
        """
        return "".join(crypt.LETTER_TO_DIGIT.get(ch, "00") for ch in message)
        
    def _generate_broadcast_audio(self, mission_id: str, ciphertext: str) -> None:
        """
        Generate an audio broadcast for the given mission ID and ciphertext.
        
        Args:
            mission_id: The mission ID to include in the broadcast
            ciphertext: The encrypted message to broadcast
        """
        try:
            generate_broadcast(mission_id, ciphertext)
            logging.info(f"Generated broadcast for mission {mission_id}")
        except Exception as e:
            error_msg = f"Failed to generate broadcast: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

    def on_generate_clicked(self) -> None:
        """
        Handle Generate button click to create a broadcast from the current mission.
        
        This method validates the input, encrypts the message using the one-time pad,
        generates an audio broadcast, and updates the mission data.
        """
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
            
        if self.encryption_key is None:
            logging.error("Cannot generate broadcast: No encryption key available")
            QMessageBox.critical(self, "Error", "Encryption key is required to generate a broadcast")
            return
        
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Broadcast Generation",
            "The first row in the pad will be used and removed after generation. "
            "The broadcast generation may take a while to complete. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Encode the message to digits
                encoded_message = self._encode_message(message)
                logging.debug(f"Encoded message: {encoded_message}")

                # Prepare the pad row by removing spaces
                pad_row = data[0].strip().replace(" ", "")

                # Encrypt the message using the one-time pad
                ciphertext = crypt.otp_mod_encrypt(encoded_message, pad_row)
                logging.debug(f"Generated ciphertext: {ciphertext}")

                # Generate the audio broadcast
                self._generate_broadcast_audio(self.current_mission.id, ciphertext)
                
                # Remove the first row from the pad data
                data = data[1:]  # Skip the first row
                updated_pad_data = "\n".join(data)
                
                # Update the mission data
                self.current_mission.update_data(updated_pad_data, self.encryption_key)
                logging.info("Updated mission data after broadcast generation")

                # Update the UI
                self.update_mission_display()
                self.broadcast_text.clear()
                
                QMessageBox.information(self, "Success", "Broadcast generated successfully and pad row removed")
            except Exception as e:
                error_msg = f"Failed to generate broadcast: {str(e)}"
                logging.error(error_msg, exc_info=True)
                QMessageBox.critical(self, "Error", error_msg)
            
    def remove_mission(self) -> None:
        """
        Remove the currently selected mission after confirmation.
        
        This method shows a confirmation dialog, removes the mission if confirmed,
        and updates the UI accordingly.
        """
        if not self.current_mission:
            logging.warning("Attempted to remove mission but no mission is selected")
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
                # Find the mission object in the missions list
                mission_to_remove = None
                for mission in self.missions:
                    if mission.id == self.current_mission.id:
                        mission_to_remove = mission
                        break

                if mission_to_remove is None:
                    error_msg = f"Could not find mission '{self.current_mission.id}' in missions list"
                    logging.error(error_msg)
                    QMessageBox.warning(self, "Warning", error_msg)
                    return

                # Remove the mission
                success = remove_mission(mission_to_remove)
                
                if success:
                    logging.info(f"Successfully removed mission '{mission_to_remove.id}'")
                    QMessageBox.information(self, "Success", f"Mission '{mission_to_remove.id}' removed successfully")
                    
                    # Update UI
                    self._clear_mission_display()
                    self.refresh_mission_list()
                else:
                    error_msg = f"Could not find mission file to remove for '{mission_to_remove.id}'"
                    logging.warning(error_msg)
                    QMessageBox.warning(self, "Warning", error_msg)
            except Exception as e:
                error_msg = f"Failed to remove mission: {str(e)}"
                logging.error(error_msg, exc_info=True)
                QMessageBox.critical(self, "Error", error_msg)
                
    def _clear_mission_display(self) -> None:
        """Clear the mission display and reset related UI elements."""
        self.current_mission = None
        self.mission_data.clear()
        self.mission_data.setRowCount(0)
        self.mission_data.setColumnCount(0)
        self.remove_mission_button.setEnabled(False)

def main() -> None:
    """
    Main entry point for the Station 3310 application.
    
    This function initializes the Qt application, creates the main window,
    and starts the application event loop.
    """
    app = QApplication(sys.argv)
    logging.info("Starting Station 3310 application")
    window = MainWindow()
    exit_code = app.exec()
    logging.info(f"Application exited with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    main()