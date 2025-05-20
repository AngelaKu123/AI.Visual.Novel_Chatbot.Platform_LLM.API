import json
import os

CHARACTER_ROOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'characters')

def get_ips():
    """List all IP folders under /characters"""
    return sorted([
        d for d in os.listdir(CHARACTER_ROOT_DIR)
        if os.path.isdir(os.path.join(CHARACTER_ROOT_DIR, d)) and d != "__pycache__"
    ])

def get_characters_by_ip(ip_name):
    """Recursively find all .json character files under an IP"""
    ip_dir = os.path.join(CHARACTER_ROOT_DIR, ip_name)
    characters = []
    for root, _, files in os.walk(ip_dir):
        for file in files:
            if file.endswith(".json"):
                rel_path = os.path.relpath(os.path.join(root, file), ip_dir)
                char_name = os.path.splitext(rel_path)[0].replace("\\", "/")  # For nested folders
                characters.append(char_name)
    return sorted(characters)

def load_character(ip_name, character_path):
    """Load character using nested folder-aware path"""
    json_path = os.path.join(CHARACTER_ROOT_DIR, ip_name, f"{character_path}.json")
    if not os.path.exists(json_path):
        raise ValueError(f"Character '{character_path}' not found in IP '{ip_name}' at {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_all_characters():
    """Load all characters across all IPs and units"""
    characters = []
    for ip in get_ips():
        for rel_path in get_characters_by_ip(ip):
            data = load_character(ip, rel_path)
            data['ip'] = ip
            data['path'] = rel_path  # Save relative path for loading again
            characters.append(data)
    return characters
