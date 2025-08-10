import base64
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QWidget, QHBoxLayout,
    QLabel, QLineEdit, QGridLayout, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator

import crypt

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