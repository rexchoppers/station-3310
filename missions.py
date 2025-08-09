import base64
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypt import generate_mission_id, generate_pad


class Mission:
    def __init__(self, mission_id):
        self.id = mission_id
        self.encrypted_id = None
        self.data = ""
        self._is_decrypted = False

    def load(self):
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
        self.encrypted_id = self.id

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
            lines = self.data

            print("Lines", lines)

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

    def encrypt(self, key):
        # Encrypt the data
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, self.data.encode('utf-8'), None)

        # Combine nonce and ciphertext and encode as base64
        encrypted_data = base64.b64encode(nonce + ciphertext)

        self.data = encrypted_data

        # Encrypt the filename
        filename_nonce = os.urandom(12)
        filename_ciphertext = aesgcm.encrypt(filename_nonce, self.id.encode('utf-8'), None)
        encrypted_filename = base64.b64encode(filename_nonce + filename_ciphertext).decode('utf-8')
        encrypted_filename = encrypted_filename.replace('/', '_').replace('+', '-').replace('=', '')

        self.id = encrypted_filename

    def is_decrypted(self):
        return self._is_decrypted

    def get_data(self):
        return self.data


def get_missions(key):
    from pathlib import Path

    current_dir = Path(__file__).parent
    missions_dir = (current_dir / "missions").resolve()

    missions = []

    if not missions_dir.exists():
        return missions

    for item in missions_dir.iterdir():
        if item.is_dir() or item.suffix.lower() != '.txt':
            continue

        encrypted_mission_id = item.stem

        mission = Mission(encrypted_mission_id)
        mission.load()

        mission.decrypt(key)
        missions.append(mission)
    return missions


def add_mission(key):
    mission_id = generate_mission_id()
    pad = generate_pad()

    current_dir = Path(__file__).parent
    missions_dir = (current_dir / "missions").resolve()

    # Create missions directory if it doesn't exist
    if not missions_dir.exists():
        missions_dir.mkdir(parents=True)

    mission = Mission(mission_id)

    for row in pad:
        mission.data += row + '\n'

    mission.encrypt(key)

    mission_file = missions_dir / f"{mission.id}.txt"
    with open(mission_file, 'wb') as f:
        f.write(mission.data)

    return mission


def remove_mission(mission):
    try:
        current_dir = Path(__file__).parent
        missions_dir = (current_dir / "missions").resolve()

        mission_file = missions_dir / f"{mission.encrypted_id}.txt"
        
        if mission_file.exists():
            mission_file.unlink()
            return True
        else:
            return False
    except Exception as e:
        print(f"Error removing mission: {e}")
        return False
