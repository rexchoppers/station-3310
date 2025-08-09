import secrets
import string


def generate_mission_id():
    alphabet = string.ascii_uppercase + string.digits

    mission_id = ''.join(secrets.choice(alphabet) for _ in range(5))

    return mission_id

def generate_pad(pages=100, groups_per_page=10, group_length=10):
    alphabet = string.ascii_uppercase
    pad = []
    for _ in range(pages):
        page = []
        for _ in range(groups_per_page):
            group = ''.join(secrets.choice(alphabet) for _ in range(group_length))
            page.append(group)
        pad.append(' '.join(page))
    return pad