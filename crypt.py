import base64
import secrets
import string

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

LETTER_TO_DIGIT = {chr(i + 65): f"{i + 1:02d}" for i in range(26)}
LETTER_TO_DIGIT[' '] = "00"

def generate_mission_id() -> str:
    alphabet = string.ascii_uppercase + string.digits

    mission_id = ''.join(secrets.choice(alphabet) for _ in range(5))

    return mission_id

def generate_pad(pages=100, groups_per_page=10, group_length=5) -> list[str]:
    digits = string.digits

    pad = []
    for _ in range(pages):
        page = []
        for _ in range(groups_per_page):
            group = ''.join(secrets.choice(digits) for _ in range(group_length))
            page.append(group)
        pad.append(' '.join(page))
    return pad

def otp_mod_encrypt(message_digits: str, pad_digits: str) -> str:
    if len(pad_digits) < len(message_digits):
        raise ValueError("Pad is too short for this message")

    cipher_digits = []
    for m_dig, p_dig in zip(message_digits, pad_digits):
        s = (int(m_dig) + int(p_dig)) % 10
        cipher_digits.append(str(s))
    return ''.join(cipher_digits)

def otp_mod_decrypt(ciphertext_digits: str, pad_digits: str) -> str:
    if len(pad_digits) < len(ciphertext_digits):
        raise ValueError("Pad is too short for this message")

    original_digits = []
    for c_dig, p_dig in zip(ciphertext_digits, pad_digits):
        diff = (int(c_dig) - int(p_dig)) % 10
        original_digits.append(str(diff))

    return ''.join(original_digits)

def generate_and_save_key(filepath: str):
    key = AESGCM.generate_key(bit_length=256)  # bytes
    # Encode to base64 string
    b64_key = base64.b64encode(key).decode('utf-8')
    # Save to file
    with open(filepath, 'w') as f:
        f.write(b64_key)
    print(f"Key saved to {filepath}")