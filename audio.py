from pydub import AudioSegment
import datetime
import os

audio_mapping = {
    "0": {
        "audio": "resources/zero.mp3",
        "cutoff": 1000
    },
    "1": {
        "audio": "resources/one.mp3",
        "cutoff": 1000
    },
    "2": {
        "audio": "resources/two.mp3",
        "cutoff": 1000
    },
    "3": {
        "audio": "resources/three.mp3",
        "cutoff": 1000
    },
    "4": {
        "audio": "resources/four.mp3",
        "cutoff": 1000
    },
    "5": {
        "audio": "resources/five.mp3",
        "cutoff": 1000
    },
    "6": {
        "audio": "resources/six.mp3",
        "cutoff": 1000
    },
    "7": {
        "audio": "resources/seven.mp3",
        "cutoff": 1000
    },
    "8": {
        "audio": "resources/eight.mp3",
        "cutoff": 1000
    },
    "9": {
        "audio": "resources/nine.mp3",
        "cutoff": 1000
    },
    "A": {
        "audio": "resources/alfa.mp3",
        "cutoff": 1000
    },
    "B": {
        "audio": "resources/bravo.mp3",
        "cutoff": 1000
    },
    "C": {
        "audio": "resources/charlie.mp3",
        "cutoff": 1000
    },
    "D": {
        "audio": "resources/delta.mp3",
        "cutoff": 1000
    },
    "E": {
        "audio": "resources/echo.mp3",
        "cutoff": 1000
    },
    "F": {
        "audio": "resources/foxtrot.mp3",
        "cutoff": 1000
    },
    "G": {
        "audio": "resources/golf.mp3",
        "cutoff": 1000
    },
    "H": {
        "audio": "resources/hotel.mp3",
        "cutoff": 1000
    },
    "I": {
        "audio": "resources/india.mp3",
        "cutoff": 1000
    },
    "J": {
        "audio": "resources/juliett.mp3",
        "cutoff": 1000
    },
    "K": {
        "audio": "resources/kilo.mp3",
        "cutoff": 1000
    },
    "L": {
        "audio": "resources/lima.mp3",
        "cutoff": 1000
    },
    "M": {
        "audio": "resources/mike.mp3",
        "cutoff": 1000
    },
    "N": {
        "audio": "resources/november.mp3",
        "cutoff": 1000
    },
    "O": {
        "audio": "resources/oscar.mp3",
        "cutoff": 1000
    },
    "P": {
        "audio": "resources/papa.mp3",
        "cutoff": 1000
    },
    "Q": {
        "audio": "resources/quebec.mp3",
        "cutoff": 1000
    },
    "R": {
        "audio": "resources/romeo.mp3",
        "cutoff": 1000
    },
    "S": {
        "audio": "resources/sierra.mp3",
        "cutoff": 1000
    },
    "T": {
        "audio": "resources/tango.mp3",
        "cutoff": 1000
    },
    "U": {
        "audio": "resources/uniform.mp3",
        "cutoff": 1000
    },
    "V": {
        "audio": "resources/victor.mp3",
        "cutoff": 1000
    },
    "W": {
        "audio": "resources/whiskey.mp3",
        "cutoff": 1000
    },
    "X": {
        "audio": "resources/xray.mp3",
        "cutoff": 1000
    },
    "Y": {
        "audio": "resources/yankee.mp3",
        "cutoff": 1000
    },
    "Z": {
        "audio": "resources/zulu.mp3",
        "cutoff": 1000
    }
}

def append_mission_id_segment(audio, mission_id):
    # Split the mission_id into individual characters
    mission_id_chars = list(mission_id)

    for char in mission_id_chars:
        if char in audio_mapping:
            audio_file = audio_mapping[char]["audio"]
            cutoff = audio_mapping[char]["cutoff"]
            # Load the audio segment and cut it to the specified duration
            segment = AudioSegment.from_mp3(audio_file)[:cutoff]
            audio += segment
        else:
            print(f"Warning: No audio mapping found for character '{char}' in mission ID.")

    return audio

def generate_broadcast(mission_id, ciphertext):
    print(mission_id)
    print(ciphertext)

    broadcast_audio = (
        AudioSegment.from_mp3("resources/jingle.mp3") +
        AudioSegment.silent(duration=2000) +
        AudioSegment.from_mp3("resources/jingle.mp3") +
        AudioSegment.silent(duration=2000) +
        AudioSegment.from_mp3("resources/jingle.mp3") +
        AudioSegment.silent(duration=2000)
    )


    # Add the mission ID to the audio + repeat 5 times
    for _ in range(5):
        broadcast_audio = append_mission_id_segment(broadcast_audio, mission_id)
        broadcast_audio += AudioSegment.silent(duration=1000)

    # Add howler for message segment
    broadcast_audio += AudioSegment.silent(duration=1000)
    broadcast_audio += (AudioSegment.from_mp3("resources/howler.mp3")[:2000] - 5)

    # Add a pause before the message
    broadcast_audio += AudioSegment.silent(duration=1000)

    # Group the encoded message into groups of 5 numbers
    for i in range(0, len(ciphertext), 5):
        segment = ciphertext[i:i+5]

        # For each character group, repeat it 5 times
        for _ in range(5):
            for char in segment:
                broadcast_audio += AudioSegment.from_mp3(audio_mapping[char]["audio"])[:audio_mapping[char]["cutoff"]]

            broadcast_audio += AudioSegment.silent(duration=2000)  # Add a pause after each group

    # Message end howl
    broadcast_audio += (AudioSegment.from_mp3("resources/howler.mp3")[:2000] - 5)

    # Format current date and time
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Export to output directory with date and time in filename
    output_path = os.path.join(output_dir, f"{formatted_time}.mp3")
    broadcast_audio.export(output_path, format="mp3")