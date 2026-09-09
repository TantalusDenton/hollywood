from ...models.schemas import Character, StoryAnalysis

CHARACTER_SYSTEM = """You are Hollywood's casting and continuity agent. Identify only recurring characters
that need stable visual identity. Separate main, supporting, and background archetypes through category.
Describe canonical visual facts, not actor names. Return the requested Pydantic structure only."""


def character_extraction_prompt(analysis: StoryAnalysis) -> str:
    return f"""Story foundation:\n{analysis.model_dump_json(indent=2)}\n\nCreate canonical, reusable visual descriptions for recurring characters."""


def character_reference_prompt(character: Character, analysis: StoryAnalysis) -> str:
    return (
        f"Full-body cinematic character reference of {character.name}: {character.visual_description}. "
        f"Role: {character.role}. Clothing: {character.clothing}. Face: {character.face}. Hair: {character.hair}. "
        f"Neutral, story-appropriate lighting. Isolated readable silhouette, no text, no contact sheet. "
        f"Visual direction: {analysis.style_bible.visual_style}; palette: {analysis.style_bible.color_palette}."
    )
