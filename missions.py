"""
Missions Module for Station 3310

This module provides functionality for managing encrypted missions,
including creating, loading, encrypting, decrypting, and removing missions.
"""

import base64
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypt import generate_mission_id, generate_pad


class Mission:
    """
    Class representing a mission with encrypted data.
    
    This class handles loading, encrypting, decrypting, and updating mission data.
    Mission IDs and data are encrypted using AES-GCM encryption.
    """
    
    def __init__(self, mission_id: str) -> None:
        """
        Initialize a mission with the given ID.
        
        Args:
            mission_id: The ID of the mission (can be encrypted or decrypted)
        """
        self.id = mission_id
        self.encrypted_id: Optional[str] = None
        self.data: Union[str, bytes] = ""
        self._is_decrypted: bool = False
        logging.debug(f"Initialized mission with ID: {mission_id}")

    def load(self) -> None:
        """
        Load mission data from file.
        
        Raises:
            FileNotFoundError: If the mission file does not exist
        """
        current_dir = Path(__file__).parent
        missions_dir = (current_dir / "missions").resolve()
        logging.debug(f"Loading mission from directory: {missions_dir}")

        # Check if the mission ID is already an encrypted filename
        mission_file = missions_dir / f"{self.id}.txt"

        if mission_file.exists():
            try:
                with open(mission_file, 'r', encoding='utf-8') as f:
                    self.data = f.read()
                logging.info(f"Loaded mission data from: {mission_file}")
            except Exception as e:
                error_msg = f"Failed to read mission file: {str(e)}"
                logging.error(error_msg)
                raise IOError(error_msg) from e
        else:
            error_msg = f"Mission {self.id} not found"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

    def decrypt(self, key: bytes) -> bool:
        """
        Decrypt the mission ID and data using the provided key.
        
        Args:
            key: The encryption key to use for decryption
            
        Returns:
            True if decryption was successful, False otherwise
        """
        # Store the encrypted ID for later use
        self.encrypted_id = self.id

        # If already decrypted, return True
        if self._is_decrypted:
            logging.debug("Mission already decrypted")
            return True

        logging.debug(f"Attempting to decrypt mission: {self.id}")
        
        try:
            aesgcm = AESGCM(key)
            
            # First, decrypt the mission ID
            if not self._decrypt_mission_id(aesgcm):
                return False
                
            # Then, decrypt the mission data
            if not self._decrypt_mission_data(aesgcm):
                return False
                
            # If both decryption steps succeeded, mark as decrypted
            self._is_decrypted = True
            logging.info(f"Successfully decrypted mission: {self.id}")
            return True
            
        except Exception as e:
            logging.error(f"Decryption failed: {str(e)}", exc_info=True)
            return False
            
    def _decrypt_mission_id(self, aesgcm: AESGCM) -> bool:
        """
        Decrypt the mission ID using the provided AESGCM instance.
        
        Args:
            aesgcm: The AESGCM instance to use for decryption
            
        Returns:
            True if decryption was successful, False otherwise
        """
        try:
            # Prepare the filename for base64 decoding
            padded_filename = self.id
            padded_filename = padded_filename.replace('_', '/').replace('-', '+')
            
            # Add padding if needed
            padding_needed = len(padded_filename) % 4
            if padding_needed:
                padded_filename += '=' * (4 - padding_needed)

            # Decode the filename
            encrypted_bytes = base64.b64decode(padded_filename)

            # Extract nonce and ciphertext
            filename_nonce = encrypted_bytes[:12]
            filename_ciphertext = encrypted_bytes[12:]

            # Decrypt the filename
            decrypted_filename = aesgcm.decrypt(filename_nonce, filename_ciphertext, None).decode('utf-8')

            # Update the ID with the decrypted version
            self.id = decrypted_filename
            logging.debug(f"Decrypted mission ID: {self.id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to decrypt mission ID: {str(e)}")
            return False
            
    def _decrypt_mission_data(self, aesgcm: AESGCM) -> bool:
        """
        Decrypt the mission data using the provided AESGCM instance.
        
        Args:
            aesgcm: The AESGCM instance to use for decryption
            
        Returns:
            True if decryption was successful, False otherwise
        """
        try:
            # Decode the data as base64
            encrypted_bytes = base64.b64decode(self.data)

            # Extract nonce and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            # Decrypt the data
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # Parse the decrypted data
            self.data = plaintext.decode('utf-8')
            logging.debug("Successfully decrypted mission data")
            return True
            
        except Exception as e:
            logging.error(f"Failed to decrypt mission data: {str(e)}")
            return False

    def encrypt(self, key: bytes) -> None:
        """
        Encrypt the mission ID and data using the provided key.
        
        Args:
            key: The encryption key to use for encryption
        """
        logging.debug(f"Encrypting mission: {self.id}")
        
        try:
            aesgcm = AESGCM(key)
            
            # Encrypt the data
            self._encrypt_mission_data(aesgcm)
            
            # Encrypt the filename
            self._encrypt_mission_id(aesgcm)
            
            # Mark as not decrypted
            self._is_decrypted = False
            logging.info(f"Successfully encrypted mission: {self.id}")
            
        except Exception as e:
            logging.error(f"Encryption failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to encrypt mission: {str(e)}") from e
            
    def _encrypt_mission_data(self, aesgcm: AESGCM) -> None:
        """
        Encrypt the mission data using the provided AESGCM instance.
        
        Args:
            aesgcm: The AESGCM instance to use for encryption
        """
        # Generate a random nonce
        nonce = os.urandom(12)
        
        # Encrypt the data
        ciphertext = aesgcm.encrypt(nonce, self.data.encode('utf-8'), None)

        # Combine nonce and ciphertext and encode as base64
        encrypted_data = base64.b64encode(nonce + ciphertext)
        self.data = encrypted_data
        logging.debug("Successfully encrypted mission data")
        
    def _encrypt_mission_id(self, aesgcm: AESGCM) -> None:
        """
        Encrypt the mission ID using the provided AESGCM instance.
        
        Args:
            aesgcm: The AESGCM instance to use for encryption
        """
        # Generate a random nonce
        filename_nonce = os.urandom(12)
        
        # Encrypt the filename
        filename_ciphertext = aesgcm.encrypt(filename_nonce, self.id.encode('utf-8'), None)
        
        # Encode as URL-safe base64
        encrypted_filename = base64.b64encode(filename_nonce + filename_ciphertext).decode('utf-8')
        encrypted_filename = encrypted_filename.replace('/', '_').replace('+', '-').replace('=', '')

        # Store the encrypted ID
        self.encrypted_id = self.id
        self.id = encrypted_filename
        logging.debug(f"Successfully encrypted mission ID: {self.id}")

    def is_decrypted(self) -> bool:
        """
        Check if the mission is currently decrypted.
        
        Returns:
            True if the mission is decrypted, False otherwise
        """
        return self._is_decrypted

    def get_data(self) -> Union[str, bytes]:
        """
        Get the mission data.
        
        Returns:
            The mission data (decrypted or encrypted)
        """
        return self.data
        
    def update_data(self, new_data: str, key: bytes) -> bool:
        """
        Update the mission data and save it back to the file.
        
        Args:
            new_data: The new data to save
            key: The encryption key to use
            
        Returns:
            True if the update was successful, False otherwise
        """
        logging.info(f"Updating data for mission: {self.id}")
        
        try:
            # Update the data
            self.data = new_data

            # Re-encrypt the data
            self.encrypt(key)
            
            # Save the updated data to the file
            self._save_to_file()
                
            # Decrypt again to restore the decrypted state
            self.decrypt(key)
            
            logging.info("Mission data updated successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update mission data: {str(e)}", exc_info=True)
            return False
            
    def _save_to_file(self) -> None:
        """
        Save the mission data to a file.
        
        Raises:
            IOError: If the file cannot be written
        """
        current_dir = Path(__file__).parent
        missions_dir = (current_dir / "missions").resolve()
        
        # Ensure the missions directory exists
        if not missions_dir.exists():
            missions_dir.mkdir(parents=True)
            logging.debug(f"Created missions directory: {missions_dir}")
        
        # Determine the filename
        filename = self.encrypted_id if self.encrypted_id else self.id
        mission_file = missions_dir / f"{filename}.txt"
        
        try:
            # Write the data to the file
            with open(mission_file, 'wb') as f:
                f.write(self.data)
            logging.debug(f"Saved mission data to: {mission_file}")
        except Exception as e:
            error_msg = f"Failed to write mission file: {str(e)}"
            logging.error(error_msg)
            raise IOError(error_msg) from e


def get_missions(key: bytes) -> List[Mission]:
    """
    Get all missions from the missions directory.
    
    This function loads all mission files from the missions directory,
    decrypts them using the provided key, and returns them as a list.
    
    Args:
        key: The encryption key to use for decryption
        
    Returns:
        A list of decrypted Mission objects
    """
    logging.info("Loading all missions")
    
    current_dir = Path(__file__).parent
    missions_dir = (current_dir / "missions").resolve()

    missions: List[Mission] = []

    # If the missions directory doesn't exist, return an empty list
    if not missions_dir.exists():
        logging.warning(f"Missions directory does not exist: {missions_dir}")
        return missions

    # Iterate through all files in the missions directory
    for item in missions_dir.iterdir():
        # Skip directories and non-text files
        if item.is_dir() or item.suffix.lower() != '.txt':
            continue

        encrypted_mission_id = item.stem
        logging.debug(f"Found mission file: {encrypted_mission_id}")

        try:
            # Create a mission object and load its data
            mission = Mission(encrypted_mission_id)
            mission.load()

            # Attempt to decrypt the mission
            if mission.decrypt(key):
                missions.append(mission)
                logging.debug(f"Successfully loaded and decrypted mission: {mission.id}")
            else:
                logging.warning(f"Failed to decrypt mission: {encrypted_mission_id}")
        except Exception as e:
            logging.error(f"Error loading mission {encrypted_mission_id}: {str(e)}")
            # Continue with the next mission
            continue
            
    logging.info(f"Loaded {len(missions)} missions")
    return missions


def add_mission(key: bytes) -> Mission:
    """
    Create a new mission with a random ID and one-time pad.
    
    This function generates a new mission with a random ID and one-time pad,
    encrypts it using the provided key, and saves it to a file.
    
    Args:
        key: The encryption key to use for encryption
        
    Returns:
        The newly created Mission object
        
    Raises:
        RuntimeError: If the mission cannot be created or saved
    """
    logging.info("Creating new mission")
    
    try:
        # Generate a random mission ID and one-time pad
        mission_id = generate_mission_id()
        logging.debug(f"Generated mission ID: {mission_id}")
        
        pad = generate_pad()
        logging.debug(f"Generated one-time pad with {len(pad)} pages")

        # Create the missions directory if it doesn't exist
        current_dir = Path(__file__).parent
        missions_dir = (current_dir / "missions").resolve()
        
        if not missions_dir.exists():
            missions_dir.mkdir(parents=True)
            logging.debug(f"Created missions directory: {missions_dir}")

        # Create a new mission with the generated ID
        mission = Mission(mission_id)

        # Add the pad data to the mission
        mission.data = '\n'.join(pad)

        # Encrypt the mission
        mission.encrypt(key)

        # Save the mission to a file
        mission_file = missions_dir / f"{mission.id}.txt"
        with open(mission_file, 'wb') as f:
            f.write(mission.data)
        logging.info(f"Saved new mission to: {mission_file}")

        return mission
        
    except Exception as e:
        error_msg = f"Failed to create mission: {str(e)}"
        logging.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e


def remove_mission(mission: Mission) -> bool:
    """
    Remove a mission by deleting its file.
    
    Args:
        mission: The Mission object to remove
        
    Returns:
        True if the mission was successfully removed, False otherwise
    """
    if not mission or not mission.encrypted_id:
        logging.error("Cannot remove mission: Invalid mission or missing encrypted ID")
        return False
        
    logging.info(f"Removing mission: {mission.id}")
    
    try:
        current_dir = Path(__file__).parent
        missions_dir = (current_dir / "missions").resolve()

        mission_file = missions_dir / f"{mission.encrypted_id}.txt"
        
        if mission_file.exists():
            mission_file.unlink()
            logging.info(f"Successfully removed mission file: {mission_file}")
            return True
        else:
            logging.warning(f"Mission file does not exist: {mission_file}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to remove mission: {str(e)}", exc_info=True)
        return False
