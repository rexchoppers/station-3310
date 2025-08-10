# Station 3310

A numbers station simulator for creating, managing, and broadcasting encrypted messages using one-time pad cryptography.

## Description

Station 3310 is a desktop application that simulates the operation of a numbers station - a shortwave radio station that broadcasts encrypted messages to covert agents. The application allows users to:

- Create and manage missions with one-time pads
- Generate PDF documents containing one-time pad data
- Encrypt messages using one-time pad cryptography
- Generate audio broadcasts of encrypted messages using phonetic alphabet and numbers
- Decode encrypted messages using a dedicated decode interface

The application uses modern cryptography (AES-GCM) for secure storage of mission data, while employing classic one-time pad encryption for the actual messages, which is authentic to real numbers station operations.

## Features

- **Mission Management**: Create, view, and remove missions, each with its own one-time pad
- **One-Time Pad Generation**: Automatically generate secure one-time pads for each mission
- **PDF Generation**: Create "TOP SECRET" documents containing one-time pad data
- **Message Encryption**: Encrypt messages using one-time pad cryptography
- **Audio Broadcast Generation**: Create authentic-sounding numbers station broadcasts with:
  - Station jingle
  - Mission ID announcement
  - Encrypted message transmission using phonetic alphabet and numbers
- **Secure Storage**: All mission data is encrypted using AES-GCM
- **Decode Interface**: Dedicated interface for decoding messages without needing to create missions

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/station-3310.git
   cd station-3310
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Generate an encryption key (if you don't have one):
   ```
   python -c "import crypt; crypt.generate_and_save_key('key.txt')"
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. Enter your encryption key when prompted, or select "Decode Only" mode if you only need to decode messages.

3. To create a new mission:
   - Click the "Add Mission" button
   - A PDF containing the one-time pad will be generated and opened automatically

4. To generate a broadcast:
   - Select a mission from the list
   - Enter a message in the text field (max 25 characters, letters and spaces only)
   - Click "Generate"
   - The broadcast will be saved as an MP3 file in the "output" directory

5. To decode a message:
   - Enter the one-time pad digits in the "Pad" row
   - Enter the cipher digits in the "Cipher" row
   - The decoded message will appear automatically in the result display

## File Structure

- **main.py**: Main application entry point and GUI implementation
- **audio.py**: Audio broadcast generation functionality
- **document.py**: PDF document generation for one-time pads
- **missions.py**: Mission management and storage
- **crypt.py**: Cryptographic operations (encryption, decryption, key generation)
- **decode.py**: Decode window implementation
- **resources/**: Audio files for phonetic alphabet, numbers, and sound effects
- **missions/**: Encrypted mission files
- **output/**: Generated audio broadcasts

## Security Notes

- The application uses AES-GCM for encrypting mission data
- One-time pad encryption is used for the actual messages
- Keep your encryption key secure - without it, you won't be able to access your missions
- Each pad row is used only once and then removed from the mission data

## License
See the [LICENSE](LICENSE) file for details.