"""
Mission handling module for Station 3310
"""
import base64
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from crypt import generate_mission_id, generate_pad


class Mission:
    def __init__(self, mission_id):
        self.id = mission_id
        self.data = ""
        self._is_decrypted = False
        
        # Load the encrypted mission data
        self._load_mission_data()
    
    def _load_mission_data(self):
        current_dir = Path(__file__).parent
        missions_dir = (current_dir / "missions").resolve()
        
        # Check if the mission ID is already an encrypted filename
        mission_file = missions_dir / f"{self.id}.txt"
        
        if mission_file.exists():
            with open(mission_file, 'r', encoding='utf-8') as f:
                self.encrypted_data = f.read()
        else:
            # If not found directly, it might be a mission ID that needs to be matched to an encrypted filename
            found = False
            for item in missions_dir.iterdir():
                if item.is_file() and item.suffix.lower() == ".txt":
                    # This is a potential encrypted mission file
                    encrypted_filename = item.stem
                    # We'll check if this matches our mission ID when decrypted in the decrypt method
                    mission_file = item
                    with open(mission_file, 'r', encoding='utf-8') as f:
                        self.encrypted_data = f.read()
                        self.encrypted_filename = encrypted_filename
                        found = True
                        break
            
            if not found:
                raise FileNotFoundError(f"Mission {self.id} not found")
    
    def decrypt(self, key):
        """
        Decrypt the mission data using the provided key
        
        Args:
            key (bytes or str): The decryption key, either as bytes or base64-encoded string
        
        Returns:
            bool: True if decryption was successful, False otherwise
        """
        if self._is_decrypted:
            return True
            
        try:
            # Convert key from base64 if it's a string
            if isinstance(key, str):
                key = base64.b64decode(key)
            
            # Ensure key is the correct length for AESGCM (16, 24, or 32 bytes)
            key_len = len(key)
            if key_len not in (16, 24, 32):  # 128, 192, or 256 bits
                print(f"Warning: Invalid key length ({key_len} bytes). AESGCM requires 16, 24, or 32 bytes.")
                return False
                
            aesgcm = AESGCM(key)
            
            # If we have an encrypted filename and we're using a mission ID to look up
            # Try to decrypt all filenames to find a match
            if hasattr(self, 'encrypted_filename'):
                try:
                    # Restore any base64 padding that might have been removed
                    padded_filename = self.encrypted_filename
                    # Replace URL-safe characters back to base64 standard
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
                    
                    # If the decrypted filename matches our mission ID, we found the right file
                    if decrypted_filename == self.id:
                        # We found the right file, continue with decryption of content
                        pass
                    else:
                        # This is not the right file, skip it
                        return False
                except Exception as e:
                    print(f"Filename decryption error: {e}")
                    return False
            
            # If we have encrypted data, decrypt it
            if hasattr(self, 'encrypted_data'):
                # Parse the encrypted data
                lines = self.encrypted_data.strip().split('\n')
                
                # First line might contain the nonce
                if len(lines) > 0:
                    try:
                        # Try to decode the first line as base64
                        encrypted_bytes = base64.b64decode(lines[0])
                        
                        # Extract nonce and ciphertext
                        nonce = encrypted_bytes[:12]
                        ciphertext = encrypted_bytes[12:]
                        
                        # Decrypt the data
                        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                        
                        # Parse the decrypted JSON data
                        self.data = plaintext.decode('utf-8')
                        self._is_decrypted = True
                        return True
                    except Exception as e:
                        print(f"Decryption error: {e}")
                        return False
            
            return False
        except Exception as e:
            print(f"Error during decryption: {e}")
            return False
    
    def is_decrypted(self):
        return self._is_decrypted
    
    def get_data(self):
        return self.data


def get_missions():
    """
    Get all available missions from the missions directory
    
    Returns:
        list: List of Mission objects
    """
    from pathlib import Path
    
    # Get the absolute path to the missions directory
    current_dir = Path(__file__).parent
    missions_dir = (current_dir / "missions").resolve()
    
    missions = []
    
    # Check if missions directory exists
    if not missions_dir.exists():
        return missions
    
    # Iterate through each mission directory
    for item in missions_dir.iterdir():
        if item.is_dir():
            # Create a Mission object for each directory
            mission_id = item.name
            try:
                mission = Mission(mission_id)
                missions.append(mission)
                print(f"Found mission: {mission_id}")
            except Exception as e:
                print(f"Error loading mission {mission_id}: {e}")
        elif item.is_file() and item.suffix.lower() == ".txt":
            # For encrypted files, we'll need to try to decrypt them
            # The filename is encrypted, so we can't directly use it as the mission ID
            # We'll need to try to decrypt it with the key when loading missions
            encrypted_filename = item.stem
            try:
                # We'll pass the encrypted filename as the mission ID
                # The Mission class will handle decryption when provided with a key
                mission = Mission(encrypted_filename)
                missions.append(mission)
                print(f"Found encrypted mission file: {encrypted_filename}")
            except Exception as e:
                print(f"Error loading encrypted mission file {encrypted_filename}: {e}")
        elif item.is_file() and item.suffix.lower() == ".map":
            # Skip old mapping files if they exist
            continue
    
    return missions


def add_mission(key, mission_data=None):
    mission_id = generate_mission_id()
    pad = generate_pad()
    
    # If no mission data provided, use the pad as the raw mission data
    if mission_data is None:
        mission_data = pad
    
    # Convert to string if needed
    if isinstance(mission_data, (dict, list)):
        json_data = json.dumps(mission_data)
    else:
        json_data = str(mission_data)
    
    # Encrypt the data
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, json_data.encode('utf-8'), None)
    
    # Combine nonce and ciphertext and encode as base64
    encrypted_data = base64.b64encode(nonce + ciphertext)
    
    # Get the missions directory path
    current_dir = Path(__file__).parent
    missions_dir = (current_dir / "missions").resolve()
    
    # Create missions directory if it doesn't exist
    if not missions_dir.exists():
        missions_dir.mkdir(parents=True)

    # Encrypt the filename
    filename_nonce = os.urandom(12)
    filename_ciphertext = aesgcm.encrypt(filename_nonce, mission_id.encode('utf-8'), None)
    encrypted_filename = base64.b64encode(filename_nonce + filename_ciphertext).decode('utf-8')
    # Replace any characters that might cause issues in filenames
    encrypted_filename = encrypted_filename.replace('/', '_').replace('+', '-').replace('=', '')
    
    # Save file with encrypted filename + encrypted raw pad data
    mission_file = missions_dir / f"{encrypted_filename}.txt"
    
    with open(mission_file, 'wb') as f:
        f.write(encrypted_data)
    
    # Return the mission with the original unencrypted ID for use in the application
    mission = Mission(mission_id)
    mission.decrypt(key)
    
    return mission