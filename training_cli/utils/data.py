"""
Data utilities for the Training CLI application.
Contains functions for loading and saving data to the JSON file.
"""
import os
import json
import datetime

# File to store training data
DATA_FILE = os.path.expanduser("~/.training_data.json")

def ensure_data_file_exists():
    """Ensure the data file exists and has the correct structure."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "entries": {},  # Entries organized by date
                "goals": {
                    # Default goals for common exercises
                    "pushup": {"daily": 50, "sets": 3, "weight": 0, "effective_date": "2023-01-01"},
                    "squat": {"daily": 30, "sets": 3, "weight": 0, "effective_date": "2023-01-01"},
                    "curl": {"daily": 20, "sets": 3, "weight": 5, "effective_date": "2023-01-01"}
                },
                "goal_history": {},
                "exercise_types": {
                    # Predefined exercise types with their attributes
                    "pushup": {"unit": "reps", "muscle_groups": ["chest", "triceps", "shoulders"]},
                    "squat": {"unit": "reps", "muscle_groups": ["quadriceps", "hamstrings", "glutes"]},
                    "curl": {"unit": "reps", "muscle_groups": ["biceps", "forearms"]},
                    "plank": {"unit": "seconds", "muscle_groups": ["core", "shoulders"]},
                    "run": {"unit": "km", "muscle_groups": ["cardiovascular", "legs"]}
                }
            }, f)
    else:
        # Migrate old data structure if needed
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        # Check if the data structure needs to be updated
        if "entries" in data and isinstance(data["entries"], type([])):
            # Old structure with flat list of entries
            old_entries = data["entries"]
            # Create new structure with entries organized by date
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            data["entries"] = {today: old_entries}

        # Add goals if not present
        if "goals" not in data:
            data["goals"] = {
                "pushup": {"daily": 50, "sets": 3, "weight": 0, "effective_date": "2023-01-01"},
                "squat": {"daily": 30, "sets": 3, "weight": 0, "effective_date": "2023-01-01"},
                "curl": {"daily": 20, "sets": 3, "weight": 5, "effective_date": "2023-01-01"}
            }

        # Add goal_history if not present
        if "goal_history" not in data:
            data["goal_history"] = {}

        # Update existing goals with new fields if needed
        for exercise_type, goal_data in data["goals"].items():
            if "sets" not in goal_data:
                goal_data["sets"] = 3
            if "weight" not in goal_data:
                goal_data["weight"] = 0
            if "effective_date" not in goal_data:
                goal_data["effective_date"] = "2023-01-01"

        # Add exercise_types if not present
        if "exercise_types" not in data:
            data["exercise_types"] = {
                "pushup": {"unit": "reps", "muscle_groups": ["chest", "triceps", "shoulders"]},
                "squat": {"unit": "reps", "muscle_groups": ["quadriceps", "hamstrings", "glutes"]},
                "curl": {"unit": "reps", "muscle_groups": ["biceps", "forearms"]},
                "plank": {"unit": "seconds", "muscle_groups": ["core", "shoulders"]},
                "run": {"unit": "km", "muscle_groups": ["cardiovascular", "legs"]}
            }

        # Save updated structure
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

def load_data():
    """Load training data from the data file."""
    ensure_data_file_exists()
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    """Save training data to the data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
