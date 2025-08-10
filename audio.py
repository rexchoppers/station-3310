"""
Audio Module for Station 3310

This module provides functionality for generating audio broadcasts
containing encrypted messages for spy missions.
"""

import datetime
import logging
import os
from typing import Dict, List, Optional, Tuple, Union

from pydub import AudioSegment

# Define audio file mappings for digits and letters
def _create_audio_mapping(default_cutoff: int = 1000) -> Dict[str, Dict[str, Union[str, int]]]:
    """
    Create a mapping of characters to their corresponding audio files and cutoff times.
    
    Args:
        default_cutoff: The default cutoff time in milliseconds for all audio files
        
    Returns:
        A dictionary mapping characters to their audio files and cutoff times
    """
    # Define the NATO phonetic alphabet for letters
    nato_phonetic = {
        'A': 'alfa', 'B': 'bravo', 'C': 'charlie', 'D': 'delta', 'E': 'echo',
        'F': 'foxtrot', 'G': 'golf', 'H': 'hotel', 'I': 'india', 'J': 'juliett',
        'K': 'kilo', 'L': 'lima', 'M': 'mike', 'N': 'november', 'O': 'oscar',
        'P': 'papa', 'Q': 'quebec', 'R': 'romeo', 'S': 'sierra', 'T': 'tango',
        'U': 'uniform', 'V': 'victor', 'W': 'whiskey', 'X': 'xray', 'Y': 'yankee',
        'Z': 'zulu'
    }
    
    # Define digit names
    digit_names = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }
    
    # Create the mapping
    mapping = {}
    
    # Add digits
    for digit, name in digit_names.items():
        mapping[digit] = {
            "audio": f"resources/{name}.mp3",
            "cutoff": default_cutoff
        }
    
    # Add letters
    for letter, phonetic in nato_phonetic.items():
        mapping[letter] = {
            "audio": f"resources/{phonetic}.mp3",
            "cutoff": default_cutoff
        }
    
    return mapping

# Create the audio mapping
audio_mapping = _create_audio_mapping(default_cutoff=1000)

def append_mission_id_segment(audio: AudioSegment, mission_id: str) -> AudioSegment:
    """
    Append audio segments for each character in the mission ID to an audio segment.
    
    Args:
        audio: The audio segment to append to
        mission_id: The mission ID to append
        
    Returns:
        The audio segment with the mission ID appended
    """
    logging.debug(f"Appending mission ID segment: {mission_id}")
    
    # Split the mission_id into individual characters
    mission_id_chars = list(mission_id)

    for char in mission_id_chars:
        if char in audio_mapping:
            audio_file = audio_mapping[char]["audio"]
            cutoff = audio_mapping[char]["cutoff"]
            
            try:
                # Load the audio segment and cut it to the specified duration
                segment = AudioSegment.from_mp3(audio_file)[:cutoff]
                audio += segment
                logging.debug(f"Added audio for character '{char}'")
            except Exception as e:
                logging.error(f"Failed to load audio file for character '{char}': {e}")
        else:
            logging.warning(f"No audio mapping found for character '{char}' in mission ID.")

    return audio

def generate_broadcast(mission_id: str, ciphertext: str) -> str:
    """
    Generate an audio broadcast containing a mission ID and encrypted message.
    
    This function creates an audio broadcast with the following structure:
    1. Jingle (repeated 3 times with pauses)
    2. Mission ID (repeated 5 times)
    3. Howler sound
    4. Encrypted message (grouped into 5-character segments, each repeated 5 times)
    5. Ending howler sound
    
    Args:
        mission_id: The mission ID to include in the broadcast
        ciphertext: The encrypted message to broadcast
        
    Returns:
        The path to the generated audio file
    """
    logging.info(f"Generating broadcast for mission ID: {mission_id}")
    logging.info(f"Ciphertext length: {len(ciphertext)} characters")
    
    # Create the initial broadcast audio with jingle
    broadcast_audio = _create_intro_jingle()
    
    # Add the mission ID segment
    broadcast_audio = _add_mission_id_segment(broadcast_audio, mission_id)
    
    # Add the message segment
    broadcast_audio = _add_message_segment(broadcast_audio, ciphertext)
    
    # Export the broadcast to a file
    output_path = _export_broadcast(broadcast_audio)
    
    logging.info(f"Broadcast generated and saved to: {output_path}")
    return output_path

def _create_intro_jingle() -> AudioSegment:
    """
    Create the introductory jingle for the broadcast.
    
    Returns:
        An AudioSegment containing the intro jingle
    """
    logging.debug("Creating intro jingle")
    
    try:
        jingle = AudioSegment.from_mp3("resources/jingle.mp3")
        silence = AudioSegment.silent(duration=2000)
        
        # Create a sequence of jingle + silence, repeated 3 times
        intro = jingle + silence + jingle + silence + jingle + silence
        
        return intro
    except Exception as e:
        logging.error(f"Failed to create intro jingle: {e}")
        # Return silent audio if jingle creation fails
        return AudioSegment.silent(duration=1000)

def _add_mission_id_segment(audio: AudioSegment, mission_id: str) -> AudioSegment:
    """
    Add the mission ID segment to the broadcast audio.
    
    Args:
        audio: The audio segment to add to
        mission_id: The mission ID to add
        
    Returns:
        The audio segment with the mission ID segment added
    """
    logging.debug("Adding mission ID segment")
    
    # Add the mission ID to the audio + repeat 5 times
    for i in range(5):
        audio = append_mission_id_segment(audio, mission_id)
        audio += AudioSegment.silent(duration=1000)
        logging.debug(f"Added mission ID repetition {i+1}/5")
    
    return audio

def _add_message_segment(audio: AudioSegment, ciphertext: str) -> AudioSegment:
    """
    Add the encrypted message segment to the broadcast audio.
    
    Args:
        audio: The audio segment to add to
        ciphertext: The encrypted message to add
        
    Returns:
        The audio segment with the message segment added
    """
    logging.debug("Adding message segment")
    
    try:
        # Add howler for message segment
        audio += AudioSegment.silent(duration=1000)
        howler = AudioSegment.from_mp3("resources/howler.mp3")[:2000] - 5
        audio += howler
        
        # Add a pause before the message
        audio += AudioSegment.silent(duration=1000)
        
        # Group the encoded message into groups of 5 numbers
        for i in range(0, len(ciphertext), 5):
            segment = ciphertext[i:i+5]
            logging.debug(f"Processing message segment: {segment}")
            
            # For each character group, repeat it 5 times
            for rep in range(5):
                for char in segment:
                    if char in audio_mapping:
                        char_audio = AudioSegment.from_mp3(audio_mapping[char]["audio"])[:audio_mapping[char]["cutoff"]]
                        audio += char_audio
                    else:
                        logging.warning(f"No audio mapping found for character '{char}' in ciphertext")
                
                # Add a pause after each group repetition
                audio += AudioSegment.silent(duration=2000)
                logging.debug(f"Added segment repetition {rep+1}/5")
        
        # Message end howl
        audio += howler
        
    except Exception as e:
        logging.error(f"Error adding message segment: {e}", exc_info=True)
    
    return audio

def _export_broadcast(audio: AudioSegment) -> str:
    """
    Export the broadcast audio to a file.
    
    Args:
        audio: The audio segment to export
        
    Returns:
        The path to the exported file
    """
    # Format current date and time
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.debug(f"Created output directory: {output_dir}")
    
    # Export to output directory with date and time in filename
    output_path = os.path.join(output_dir, f"{formatted_time}.mp3")
    
    try:
        audio.export(output_path, format="mp3")
        logging.debug(f"Exported broadcast to: {output_path}")
    except Exception as e:
        logging.error(f"Failed to export broadcast: {e}", exc_info=True)
    
    return output_path