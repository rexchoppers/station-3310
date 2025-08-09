import secrets
import string


def generate_mission_id():
    alphabet = string.ascii_uppercase + string.digits

    mission_id = ''.join(secrets.choice(alphabet) for _ in range(5))

    return mission_id