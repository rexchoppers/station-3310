"""
Decode Module for Station 3310

This module provides functionality for decoding encrypted messages using
one-time pad decryption. It includes a custom dialog for entering pad and
cipher values and displaying the decoded message.
"""

import base64
import logging
from typing import List, Optional, Tuple, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QWidget, QHBoxLayout,
    QLabel, QLineEdit, QGridLayout, QStyledItemDelegate,
    QTableView
)
from PyQt6.QtCore import Qt, QRegularExpression, QModelIndex
from PyQt6.QtGui import QRegularExpressionValidator

import crypt

class DigitItemDelegate(QStyledItemDelegate):
    """
    Custom item delegate to restrict input to single digits.
    
    This delegate is used for table cells that should only accept single digit inputs.
    It also provides automatic focus movement to the next cell when a digit is entered.
    """
    def __init__(self, parent: Optional[QTableView] = None) -> None:
        """
        Initialize the digit item delegate.
        
        Args:
            parent: The parent table view
        """
        super().__init__(parent)
        logging.debug("DigitItemDelegate initialized")
        
    def createEditor(self, parent: QWidget, option: Any, index: QModelIndex) -> QLineEdit:
        """
        Create a line edit with validation for digits only.
        
        Args:
            parent: The parent widget for the editor
            option: The style options for the editor
            index: The model index being edited
            
        Returns:
            A QLineEdit configured to accept only digits
        """
        editor = QLineEdit(parent)
        editor.setMaxLength(1)  # Limit to one character
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set validator to only allow digits
        validator = QRegularExpressionValidator(QRegularExpression("[0-9]"), editor)
        editor.setValidator(validator)
        
        logging.debug(f"Created digit editor for cell at {index.row()},{index.column()}")
        return editor
    
    def setModelData(self, editor: QLineEdit, model: Any, index: QModelIndex) -> None:
        """
        Set the model data and move focus to the next cell if a digit was entered.
        
        Args:
            editor: The editor containing the data to set
            model: The model to update
            index: The model index to update
        """
        text = editor.text()
        model.setData(index, text, Qt.ItemDataRole.EditRole)
        
        # If a digit was entered, move to the next cell
        if text and text.isdigit():
            # Get the table widget
            table = self.parent()
            if not isinstance(table, QTableView):
                logging.warning("Parent is not a QTableView, cannot move focus")
                return
                
            # Determine the next cell to focus
            current_row = index.row()
            current_col = index.column()
            
            # Move to the next column in the same row
            if current_col < table.columnCount() - 1:
                next_index = table.model().index(current_row, current_col + 1)
                table.setCurrentIndex(next_index)
                table.edit(next_index)
                logging.debug(f"Moved focus to next cell at {current_row},{current_col+1}")
    
    def paint(self, painter: Any, option: Any, index: QModelIndex) -> None:
        """
        Paint the delegate.
        
        Args:
            painter: The painter to use for drawing
            option: The style options to use for drawing
            index: The model index to draw
        """
        super().paint(painter, option, index)

class DecodeWindow(QDialog):
    """
    Dialog window for decoding encrypted messages using one-time pad decryption.
    
    This window provides input fields for entering pad and cipher values,
    and displays the decoded message in real-time as the values are entered.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the decode window.
        
        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Decode Only")
        self.setFixedSize(1400, 300)  # Adjusted width for 10 input fields per row
        
        # Initialize UI components
        self.input_fields: List[List[QLineEdit]] = []
        self.result_display: Optional[QLineEdit] = None
        
        self._setup_ui()
        logging.info("Decode window initialized")
        
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)  # Increased spacing for better visual separation
        
        # Set up input fields
        self._setup_input_fields(main_layout)
        
        # Set up result display
        self._setup_result_display(main_layout)
        
    def _setup_input_fields(self, main_layout: QVBoxLayout) -> None:
        """
        Set up the input fields for pad and cipher values.
        
        Args:
            main_layout: The main layout to add the input fields to
        """
        # Create a grid layout for the input fields
        input_widget = QWidget()
        input_layout = QGridLayout(input_widget)
        input_layout.setSpacing(10)  # Space between fields
        
        # Create labels for pad and cipher rows
        pad_label = QLabel("Pad:")
        pad_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        input_layout.addWidget(pad_label, 0, 0)
        
        cipher_label = QLabel("Cipher:")
        cipher_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        input_layout.addWidget(cipher_label, 1, 0)
        
        # Create 10 input fields for each row (pad and cipher)
        for row in range(2):
            row_fields: List[QLineEdit] = []
            for col in range(10):
                field = self._create_digit_input_field()
                
                # Add to layout (offset column by 1 to account for labels)
                input_layout.addWidget(field, row, col + 1)
                row_fields.append(field)
            
            self.input_fields.append(row_fields)
        
        # Add the input widget to the main layout
        main_layout.addWidget(input_widget)
        
    def _create_digit_input_field(self) -> QLineEdit:
        """
        Create a QLineEdit field configured for digit input.
        
        Returns:
            A configured QLineEdit for digit input
        """
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
        
        return field
        
    def _setup_result_display(self, main_layout: QVBoxLayout) -> None:
        """
        Set up the result display area.
        
        Args:
            main_layout: The main layout to add the result display to
        """
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        
        self.result_display = QLineEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_display.setStyleSheet("font-size: 14pt; background-color: #f0f0f0;")
        result_layout.addWidget(self.result_display)
        
        # Add the result widget to the main layout
        main_layout.addWidget(result_widget)

    
    def set_pad_value(self, value: str) -> bool:
        """
        Set the pad row value programmatically.
        
        This method distributes the provided value across the pad row input fields,
        with up to 5 digits per field.
        
        Args:
            value: The pad value to set (string of digits)
            
        Returns:
            True if the value was set successfully, False otherwise
        """
        if not value:
            logging.warning("Attempted to set empty pad value")
            return False
            
        if not value.isdigit():
            logging.warning(f"Invalid pad value (non-digit characters): {value}")
            return False
        
        logging.debug(f"Setting pad value: {value}")
        
        # Temporarily disconnect signals to prevent multiple updates
        for field in self.input_fields[0]:
            field.blockSignals(True)
        
        try:
            # Distribute the value across the pad row fields
            self._distribute_value_to_fields(value, self.input_fields[0])
            
            # Update the decoded characters
            self.update_decoded_character()
            return True
        finally:
            # Reconnect signals
            for field in self.input_fields[0]:
                field.blockSignals(False)
    
    def set_cipher_value(self, value: str) -> bool:
        """
        Set the cipher row value programmatically.
        
        This method distributes the provided value across the cipher row input fields,
        with up to 5 digits per field.
        
        Args:
            value: The cipher value to set (string of digits)
            
        Returns:
            True if the value was set successfully, False otherwise
        """
        if not value:
            logging.warning("Attempted to set empty cipher value")
            return False
            
        if not value.isdigit():
            logging.warning(f"Invalid cipher value (non-digit characters): {value}")
            return False
        
        logging.debug(f"Setting cipher value: {value}")
        
        # Temporarily disconnect signals to prevent multiple updates
        for field in self.input_fields[1]:
            field.blockSignals(True)
        
        try:
            # Distribute the value across the cipher row fields
            self._distribute_value_to_fields(value, self.input_fields[1])
            
            # Update the decoded characters
            self.update_decoded_character()
            return True
        finally:
            # Reconnect signals
            for field in self.input_fields[1]:
                field.blockSignals(False)
                
    def _distribute_value_to_fields(self, value: str, fields: List[QLineEdit]) -> None:
        """
        Distribute a value across a list of input fields.
        
        Args:
            value: The value to distribute (string of digits)
            fields: The list of input fields to distribute the value to
        """
        remaining_value = value
        
        for field in fields:
            if not remaining_value:
                field.clear()
                continue
            
            # Take up to 5 digits for each field
            field_value = remaining_value[:5]
            remaining_value = remaining_value[5:]
            field.setText(field_value)
    
    def update_decoded_character(self) -> None:
        """
        Update the decoded characters based on the input fields.
        
        This method collects the pad and cipher values from the input fields,
        decodes the message using one-time pad decryption, and displays the result.
        """
        # Clear the result display
        if self.result_display:
            self.result_display.clear()
        
        # Collect all digits from pad and cipher rows
        pad_digits = self._collect_digits_from_row(0)
        cipher_digits = self._collect_digits_from_row(1)
        
        # If we don't have any input, clear the result and return
        if not pad_digits or not cipher_digits:
            logging.debug("No input to decode")
            return
        
        # Decode the message
        decoded_text = self._decode_message(pad_digits, cipher_digits)
        
        # Display the decoded text
        if self.result_display:
            self.result_display.setText(decoded_text)
            logging.info(f"Decoded message: {decoded_text}")
            
    def _collect_digits_from_row(self, row_index: int) -> str:
        """
        Collect all digits from a row of input fields.
        
        Args:
            row_index: The index of the row to collect digits from (0 for pad, 1 for cipher)
            
        Returns:
            A string containing all digits from the specified row
        """
        if row_index < 0 or row_index >= len(self.input_fields):
            logging.error(f"Invalid row index: {row_index}")
            return ""
            
        digits = ""
        for field in self.input_fields[row_index]:
            digits += field.text()
            
        return digits
        
    def _decode_message(self, pad_digits: str, cipher_digits: str) -> str:
        """
        Decode a message using one-time pad decryption.
        
        Args:
            pad_digits: The pad digits to use for decryption
            cipher_digits: The cipher digits to decrypt
            
        Returns:
            The decoded message as text
        """
        decoded_text = ""
        min_length = min(len(pad_digits), len(cipher_digits))
        
        logging.debug(f"Decoding message with {min_length} digits")
        
        for i in range(0, min_length, 2):
            # If we don't have a complete pair, break
            if i + 1 >= min_length:
                break
            
            # Decode a single character
            decoded_char = self._decode_character(pad_digits[i:i+2], cipher_digits[i:i+2])
            decoded_text += decoded_char
        
        return decoded_text
        
    def _decode_character(self, pad_pair: str, cipher_pair: str) -> str:
        """
        Decode a single character using one-time pad decryption.
        
        Args:
            pad_pair: The pad digit pair to use for decryption
            cipher_pair: The cipher digit pair to decrypt
            
        Returns:
            The decoded character
        """
        try:
            # Decrypt the pair
            decrypted_digits = crypt.otp_mod_decrypt(cipher_pair, pad_pair)
            
            # Format the decrypted digits as a two-digit string
            formatted_digits = self._format_digit_pair(decrypted_digits)
            
            # Convert to letter
            digit_to_letter = {v: k for k, v in crypt.LETTER_TO_DIGIT.items()}
            decoded_char = digit_to_letter.get(formatted_digits, "?")
            
            return decoded_char
        except Exception as e:
            logging.error(f"Error decoding character: {e}", exc_info=True)
            return "?"
            
    def _format_digit_pair(self, digits: str) -> str:
        """
        Format a digit string as a two-digit string.
        
        Args:
            digits: The digit string to format
            
        Returns:
            A two-digit string
        """
        if len(digits) == 1:
            return "0" + digits
        elif len(digits) > 2:
            return digits[:2]
        else:
            return digits