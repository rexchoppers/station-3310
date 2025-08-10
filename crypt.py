import secrets
import string


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

def otp_mod(message_digits: str, pad_digits: str) -> str:
    if len(pad_digits) < len(message_digits):
        raise ValueError("Pad is too short for this message")

    cipher_digits = []
    for m_dig, p_dig in zip(message_digits, pad_digits):
        s = (int(m_dig) + int(p_dig)) % 10
        cipher_digits.append(str(s))
    return ''.join(cipher_digits)
