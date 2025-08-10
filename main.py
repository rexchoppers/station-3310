import base64
import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QDialog, QLineEdit, QGridLayout, QStyledItemDelegate
)

from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator, QFont

import crypt
from audio import generate_broadcast
from document import generate_spy_pad_pdf, preview_pdf_external
from missions import get_missions, add_mission, remove_mission

key = None

class DigitItemDelegate(QStyledItemDelegate):
    """Custom item delegate to restrict input to single digits"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def createEditor(self, parent, option, index):
        """Create a line edit with validation for digits only"""
        editor = QLineEdit(parent)
        editor.setMaxLength(1)  # Limit to one character
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set validator to only allow digits
        validator = QRegularExpressionValidator(QRegularExpression("[0-9]"), editor)
        editor.setValidator(validator)
        
        return editor
    
    def setModelData(self, editor, model, index):
        """Set the model data and move focus to the next cell if a digit was entered"""
        text = editor.text()
        model.setData(index, text, Qt.ItemDataRole.EditRole)
        
        # If a digit was entered, move to the next cell
        if text and text.isdigit():
            # Get the table widget
            table = self.parent()
            
            # Determine the next cell to focus
            current_row = index.row()
            current_col = index.column()
            
            # Move to the next column in the same row
            if current_col < table.columnCount() - 1:
                next_index = table.model().index(current_row, current_col + 1)
                table.setCurrentIndex(next_index)
                table.edit(next_index)
    
    def paint(self, painter, option, index):
        """Custom painting for the cells"""
        # Use default painting
        super().paint(painter, option, index)

class DecodeWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Decode Only")
        self.setFixedSize(1400, 300)  # Adjusted width for 10 input fields per row
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)  # Increased spacing for better visual separation
        
        # Create a grid layout for the input fields
        input_widget = QWidget()
        input_layout = QGridLayout(input_widget)
        input_layout.setSpacing(10)  # Space between fields
        
        # Create 10 input fields in 2 rows of 10
        self.input_fields = []
        
        # Create labels for pad and cipher rows
        pad_label = QLabel("Pad:")
        pad_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        input_layout.addWidget(pad_label, 0, 0)
        
        cipher_label = QLabel("Cipher:")
        cipher_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        input_layout.addWidget(cipher_label, 1, 0)
        
        # Create 10 input fields for each row
        for row in range(2):
            row_fields = []
            for col in range(10):
                # Create a QLineEdit with validation for digits only
                field = QLineEdit()
                field.setMaxLength(5)  # Limit to 5 characters
                field.setFixedWidth(100)  # Fixed width for all fields
                field.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Set validator to only allow digits
                validator = QRegularExpressionValidator(QRegularExpression("[0-9]{0,5}"), field)
                field.setValidator(validator)
                
                # Connect textChanged signal to update decoded characters
                field.textChanged.connect(self.update_decoded_character)
                
                # Add to layout (offset column by 1 to account for labels)
                input_layout.addWidget(field, row, col + 1)
                row_fields.append(field)
            
            self.input_fields.append(row_fields)
        
        # Add the input widget to the main layout
        main_layout.addWidget(input_widget)
        
        # Create result display area
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        
        result_label = QLabel("Decoded Characters:")
        result_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        result_layout.addWidget(result_label)
        
        self.result_display = QLineEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_display.setStyleSheet("font-size: 14pt; background-color: #f0f0f0;")
        result_layout.addWidget(self.result_display)
        
        # Add the result widget to the main layout
        main_layout.addWidget(result_widget)

    
    def set_pad_value(self, value):
        """Set the pad row value programmatically"""
        if not value:
            return False
        
        # Temporarily disconnect signals to prevent multiple updates
        for field in self.input_fields[0]:
            field.blockSignals(True)
        
        try:
            # Distribute the value across the pad row fields
            remaining_value = value
            for i, field in enumerate(self.input_fields[0]):
                if not remaining_value:
                    field.clear()
                    continue
                
                # Take up to 5 digits for each field
                field_value = remaining_value[:5]
                remaining_value = remaining_value[5:]
                field.setText(field_value)
            
            # Update the decoded characters
            self.update_decoded_character()
            return True
        finally:
            # Reconnect signals
            for field in self.input_fields[0]:
                field.blockSignals(False)
    
    def set_cipher_value(self, value):
        """Set the cipher row value programmatically"""
        if not value:
            return False
        
        # Temporarily disconnect signals to prevent multiple updates
        for field in self.input_fields[1]:
            field.blockSignals(True)
        
        try:
            # Distribute the value across the cipher row fields
            remaining_value = value
            for i, field in enumerate(self.input_fields[1]):
                if not remaining_value:
                    field.clear()
                    continue
                
                # Take up to 5 digits for each field
                field_value = remaining_value[:5]
                remaining_value = remaining_value[5:]
                field.setText(field_value)
            
            # Update the decoded characters
            self.update_decoded_character()
            return True
        finally:
            # Reconnect signals
            for field in self.input_fields[1]:
                field.blockSignals(False)
    
    def update_decoded_character(self):
        """Update the decoded characters based on the input fields"""
        # Clear the result display
        self.result_display.clear()
        
        # Collect all digits from pad and cipher rows
        pad_digits = ""
        cipher_digits = ""
        
        for field in self.input_fields[0]:  # Pad row
            pad_digits += field.text()
        
        for field in self.input_fields[1]:  # Cipher row
            cipher_digits += field.text()
        
        # If we don't have any input, clear the result and return
        if not pad_digits or not cipher_digits:
            return
        
        # Process the digits in pairs to decode characters
        decoded_text = ""
        min_length = min(len(pad_digits), len(cipher_digits))
        
        for i in range(0, min_length, 2):
            # If we don't have a complete pair, break
            if i + 1 >= min_length:
                break
            
            # Get a pair of digits from each row
            pad_pair = pad_digits[i:i+2]
            cipher_pair = cipher_digits[i:i+2]
            
            # Decrypt the pair
            decrypted_digits = crypt.otp_mod_decrypt(cipher_pair, pad_pair)
            
            # Format the decrypted digits as a two-digit string
            formatted_digits = decrypted_digits
            if len(decrypted_digits) == 1:
                formatted_digits = "0" + decrypted_digits
            elif len(decrypted_digits) > 2:
                formatted_digits = decrypted_digits[:2]
            
            # Convert to letter
            digit_to_letter = {v: k for k, v in crypt.LETTER_TO_DIGIT.items()}
            decoded_char = digit_to_letter.get(formatted_digits, "?")
            
            # Add to the decoded text
            decoded_text += decoded_char
        
        # Display the decoded text
        self.result_display.setText(decoded_text)

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
        """Open the decode window"""
        decode_window = DecodeWindow(self)
        
        # Example: Set pad and cipher values programmatically
        # This demonstrates how to use the new methods and helps diagnose the issue
        
        # We'll test with a few different examples to ensure decoding works correctly
        
        # Example 1: Letter 'A' (pad: 01, cipher: 02 -> result: 'B')
        # When pad=01 and cipher=02, the decryption should be 01 (A)
        print("\nTesting Example 1: pad=01, cipher=02")
        decode_window.set_pad_value("01")
        decode_window.set_cipher_value("02")
        
        # Example 2: Letter 'Z' (pad: 26, cipher: 36 -> result: 'K')
        # When pad=26 and cipher=36, the decryption should be 10 (J)
        print("\nTesting Example 2: pad=26, cipher=36")
        decode_window.set_pad_value("26")
        decode_window.set_cipher_value("36")
        
        # Example 3: Space character (pad: 00, cipher: 05 -> result: '5')
        # When pad=00 and cipher=05, the decryption should be 05 (5)
        print("\nTesting Example 3: pad=00, cipher=05")
        decode_window.set_pad_value("00")
        decode_window.set_cipher_value("05")
        
        # Example 4: Single-digit result (pad: 09, cipher: 10 -> result: 'A')
        # When pad=09 and cipher=10, the decryption should be 1, which should be formatted as 01 (A)
        print("\nTesting Example 4: pad=09, cipher=10")
        decode_window.set_pad_value("09")
        decode_window.set_cipher_value("10")
        
        # Show the window with the last example's values
        decode_window.exec()
        
        # If opened from the key dialog, close the application after decode window is closed
        if parent_dialog:
            parent_dialog.reject()
            sys.exit(0)
    
    def init_ui(self):
        """Initialize the main UI components"""
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