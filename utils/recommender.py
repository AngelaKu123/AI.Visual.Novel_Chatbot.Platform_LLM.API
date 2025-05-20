import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils.character_loader import load_all_characters
from utils.user_data import extract_user_tags

# Convert tags to a vector based on a unified tag universe
def tag_vector(tags, tag_universe):
    return [1 if tag in tags else 0 for tag in tag_universe]

# Compute cosine similarity between two tag vectors
def similarity_score(vec1, vec2):
    if not vec1 or not vec2:
        return 0.0
    return cosine_similarity([vec1], [vec2])[0][0]

# Match user tags against all characters
def recommend_by_tags(user_tags, all_characters, top_n=10):
    tag_universe = list(set(
        tag
        for char in all_characters
        if isinstance(char.get("tags"), list)
        for tag in char["tags"]
    ))

    if not tag_universe:
        print("⚠ Warning: No tags found in any character.")
        return []

    user_vector = tag_vector(user_tags, tag_universe)
    scored = []

    for char in all_characters:
        tags = char.get("tags", [])
        if not tags:
            continue
        char_vector = tag_vector(tags, tag_universe)
        score = similarity_score(user_vector, char_vector)
        scored.append((score, char))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [char for score, char in scored[:top_n]]

# Public API from GUI: requires user_data
def recommend_characters(user_data):
    characters = load_all_characters()
    if not characters:
        print("⚠ No characters loaded.")
        return []

    preferred_tags = extract_user_tags(user_data)
    return recommend_by_tags(preferred_tags, characters, top_n=10)