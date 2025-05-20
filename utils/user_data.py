import os
import json

USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "users")
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Load or create a user profile
def load_user(username):
    file_path = os.path.join(USER_DATA_DIR, f"{username}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        user_data = {
            "username": username,
            "interactions": {}
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=4)
        return user_data

# Save updated profile
def save_user(user_data):
    file_path = os.path.join(USER_DATA_DIR, f"{user_data['username']}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=4)

# Update interaction tags
def update_user_tags(user_data, character):
    for tag in character.get("tags", []):
        if tag:
            user_data["interactions"][tag] = user_data["interactions"].get(tag, 0) + 1
    save_user(user_data)

# Convert interactions into sorted tag list
def extract_user_tags(user_data, top_k=10):
    return sorted(
        user_data["interactions"],
        key=user_data["interactions"].get,
        reverse=True
    )[:top_k]