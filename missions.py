"""
Iterate through the missions directory
"""
def get_missions():
    from pathlib import Path
    import json

    # Get the absolute path to the missions directory
    current_dir = Path(__file__).parent
    missions_dir = (current_dir / "missions").resolve()

    missions = []

    # Iterate through each mission directory
    for mission_dir in missions_dir.iterdir():
        if mission_dir.is_dir():
            mission_name = mission_dir.name
            print(f"Found mission: {mission_name}")

            # Initialize a dictionary to hold the mission data
            mission_data = {
                "name": mission_name,
                "description": "",
                "steps": []
            }

            # Iterate through files in the mission directory
            for file_path in mission_dir.glob("**/*"):
                if file_path.is_file() and file_path.suffix.lower() == ".json":
                    print(f"  - File: {file_path.relative_to(mission_dir)}")

                    with open(file_path, 'r', encoding='utf-8') as f:
                        step_data = json.load(f)
                        mission_data["steps"].append(step_data)

            # Add the mission data to the list of missions
            missions.append(mission_data)

    return missions