import base64
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import main
from crypt import generate_mission_id, generate_pad


class Mission:
    def __init__(self, mission_id):
        self.id = mission_id
        self.data = ""
        self._is_decrypted = False

        self._load_mission_data()

    def _load_mission_data(self):
        current_dir = Path(__file__).parent
        missions_dir = (current_dir / "missions").resolve()

        # Check if the mission ID is already an encrypted filename
        mission_file = missions_dir / f"{self.id}.txt"

        if mission_file.exists():
            with open(mission_file, 'r', encoding='utf-8') as f:
                self.data = f.read()
        else:
            raise FileNotFoundError(f"Mission {self.id} not found")

    def decrypt(self, key):

        print("Decrypting mission:", self.id)
        if self._is_decrypted:
            return True

        try:
            print("Decrypt called", key)

            aesgcm = AESGCM(key)

            # Decode Mission ID
            try:
                padded_filename = self.id
                padded_filename = padded_filename.replace('_', '/').replace('-', '+')
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

                self.id = decrypted_filename
            except Exception as e:
                print(f"Filename decryption error: {e}")
                return False

            # Decrypt the mission data
            lines = self.data.strip().split('\n')

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
        except Exception as e:
            print(f"Error during decryption: {e}")
            return False

    def is_decrypted(self):
        return self._is_decrypted

    def get_data(self):
        return self.data


def get_missions():
    from pathlib import Path

    current_dir = Path(__file__).parent
    missions_dir = (current_dir / "missions").resolve()

    missions = []

    if not missions_dir.exists():
        return missions

    for item in missions_dir.iterdir():
        # Skip directories and non-txt files
        if item.is_dir() or item.suffix.lower() != '.txt':
            continue

        encrypted_mission_id = item.stem

        mission = Mission(encrypted_mission_id)
        mission.decrypt(main.key)
        missions.append(mission)
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
    encrypted_filename = encrypted_filename.replace('/', '_').replace('+', '-').replace('=', '')

    # Save file with encrypted filename + encrypted raw pad data
    mission_file = missions_dir / f"{encrypted_filename}.txt"

    with open(mission_file, 'wb') as f:
        f.write(encrypted_data)

    mission = Mission(mission_id)
    mission.decrypt(key)

    print(mission.data)

    return mission
