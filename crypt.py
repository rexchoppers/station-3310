"""
Cryptography Module for Station 3310

This module provides cryptographic functionality for the Station 3310 application,
including one-time pad encryption/decryption, mission ID generation, and key management.
"""

import base64
import logging
import secrets
import string
from typing import Dict, List, Optional, Tuple, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Mapping from letters to two-digit numbers (A=01, B=02, ..., Z=26, space=00)
LETTER_TO_DIGIT: Dict[str, str] = {chr(i + 65): f"{i + 1:02d}" for i in range(26)}
LETTER_TO_DIGIT[' '] = "00"

def generate_mission_id(length: int = 5) -> str:
    """
    Generate a random mission ID.
    
    This function creates a random mission ID consisting of uppercase letters
    and digits, which can be used to identify a mission.
    
    Args:
        length: The length of the mission ID (default: 5)
        
    Returns:
        A random mission ID string
    """
    alphabet = string.ascii_uppercase + string.digits
    
    mission_id = ''.join(secrets.choice(alphabet) for _ in range(length))
    logging.debug(f"Generated mission ID: {mission_id}")
    
    return mission_id

def generate_pad(pages: int = 100, groups_per_page: int = 10, group_length: int = 5) -> List[str]:
    """
    Generate a one-time pad for encryption.
    
    This function creates a one-time pad consisting of random digits,
    organized into pages, groups, and characters.
    
    Args:
        pages: The number of pages in the pad (default: 100)
        groups_per_page: The number of groups per page (default: 10)
        group_length: The number of digits per group (default: 5)
        
    Returns:
        A list of strings, where each string represents a page of the pad
    """
    logging.info(f"Generating one-time pad with {pages} pages")
    digits = string.digits

    pad = []
    for page_num in range(pages):
        page = []
        for group_num in range(groups_per_page):
            # Generate a random group of digits
            group = ''.join(secrets.choice(digits) for _ in range(group_length))
            page.append(group)
        
        # Join the groups with spaces to form a page
        pad.append(' '.join(page))
        
    logging.debug(f"Generated pad with {len(pad)} pages")
    return pad

def otp_mod_encrypt(message_digits: str, pad_digits: str) -> str:
    """
    Encrypt a message using one-time pad with modular addition.
    
    This function encrypts a message by adding each digit of the message
    to the corresponding digit of the pad, modulo 10.
    
    Args:
        message_digits: The message to encrypt, as a string of digits
        pad_digits: The one-time pad to use for encryption, as a string of digits
        
    Returns:
        The encrypted message as a string of digits
        
    Raises:
        ValueError: If the pad is too short for the message
    """
    if len(pad_digits) < len(message_digits):
        error_msg = f"Pad is too short for this message: {len(pad_digits)} < {len(message_digits)}"
        logging.error(error_msg)
        raise ValueError(error_msg)

    logging.debug(f"Encrypting message of length {len(message_digits)}")
    
    cipher_digits = []
    for m_dig, p_dig in zip(message_digits, pad_digits):
        # Add the message digit and pad digit, modulo 10
        encrypted_digit = (int(m_dig) + int(p_dig)) % 10
        cipher_digits.append(str(encrypted_digit))
        
    return ''.join(cipher_digits)

def otp_mod_decrypt(ciphertext_digits: str, pad_digits: str) -> str:
    """
    Decrypt a message using one-time pad with modular subtraction.
    
    This function decrypts a message by subtracting each digit of the pad
    from the corresponding digit of the ciphertext, modulo 10.
    
    Args:
        ciphertext_digits: The encrypted message, as a string of digits
        pad_digits: The one-time pad to use for decryption, as a string of digits
        
    Returns:
        The decrypted message as a string of digits
        
    Raises:
        ValueError: If the pad is too short for the ciphertext
    """
    if len(pad_digits) < len(ciphertext_digits):
        error_msg = f"Pad is too short for this message: {len(pad_digits)} < {len(ciphertext_digits)}"
        logging.error(error_msg)
        raise ValueError(error_msg)

    logging.debug(f"Decrypting message of length {len(ciphertext_digits)}")
    
    original_digits = []
    for c_dig, p_dig in zip(ciphertext_digits, pad_digits):
        # Subtract the pad digit from the ciphertext digit, modulo 10
        decrypted_digit = (int(c_dig) - int(p_dig)) % 10
        original_digits.append(str(decrypted_digit))

    return ''.join(original_digits)

def generate_and_save_key(filepath: str) -> str:
    """
    Generate a new encryption key and save it to a file.
    
    This function generates a new 256-bit AES-GCM key, encodes it as base64,
    and saves it to the specified file.
    
    Args:
        filepath: The path to save the key to
        
    Returns:
        The base64-encoded key
        
    Raises:
        IOError: If the key cannot be saved to the file
    """
    try:
        # Generate a new 256-bit key
        key = AESGCM.generate_key(bit_length=256)
        logging.info("Generated new 256-bit AES-GCM key")
        
        # Encode the key as base64
        b64_key = base64.b64encode(key).decode('utf-8')
        
        # Save the key to the specified file
        with open(filepath, 'w') as f:
            f.write(b64_key)
            
        logging.info(f"Key saved to {filepath}")
        return b64_key
    except IOError as e:
        error_msg = f"Failed to save key to {filepath}: {str(e)}"
        logging.error(error_msg)
        raise IOError(error_msg) from e