from ...models.schemas import Character, Scene, Shot, StoryAnalysis

SHOT_SYSTEM = """You are Hollywood's cinematographer. Decompose one narrative scene into coherent,
filmable video shots. Every shot needs a specific action and a beginning and ending visual state. Respect the
requested shot length and use canonical character IDs. Return only the requested Pydantic schema."""


def shot_breakdown_prompt(scene: Scene, characters: list[Character], analysis: StoryAnalysis, target_duration: int) -> str:
    cast = [character.model_dump(mode="json") for character in characters if character.id in scene.characters]
    return f"""World: {analysis.world_bible}\nStyle: {analysis.style_bible.model_dump_json()}\nScene: {scene.model_dump_json()}\nCast: {cast}\nTarget each shot at {target_duration} seconds."""


def video_prompt(shot: Shot, analysis: StoryAnalysis, character_descriptions: list[str]) -> str:
    subjects = " ".join(character_descriptions)
    return (
        f"{subjects} Location: {shot.location}. Action: {shot.action}. Camera: {shot.camera}, {shot.lens}, "
        f"{shot.framing}; movement: {shot.camera_motion}. Lighting: {shot.lighting}. Beginning: {shot.beginning_state}. "
        f"Ending: {shot.ending_state}. Style: {shot.visual_style}; {analysis.style_bible.film_grain}; "
        f"{analysis.style_bible.depth_of_field}."
    )
