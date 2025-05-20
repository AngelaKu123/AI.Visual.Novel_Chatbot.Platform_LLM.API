def generate_stable_diffusion_prompt(context, character):
    # Basic fixed keywords
    name = character['name']
    hair = character['appearance']['hair']
    eyes = character['appearance']['eyes']
    build = character['appearance']['build']
    outfit = character['outfits'][0]['description']

    # Try to guess background/location
    if "school" in context.lower():
        location = "Japanese school courtyard, cherry blossoms"
    elif "battle" in context.lower():
        location = "ruined battlefield, smoke and debris"
    elif "bedroom" in context.lower():
        location = "cozy anime bedroom, posters on walls"
    else:
        location = "anime fantasy landscape, beautiful scenery"

    # Camera angle - fallback
    if "look up" in context.lower():
        angle = "low-angle view"
    elif "look down" in context.lower():
        angle = "top-down view"
    else:
        angle = "cinematic mid-shot"

    prompt = f"""
{location}, {angle}, featuring {name}, {build} body, {hair} hair, {eyes} eyes, wearing {outfit},
high quality, detailed, anime artstyle
    """.strip().replace("\n", " ")

    return prompt
