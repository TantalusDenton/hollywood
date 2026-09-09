from ...models.schemas import GenerationSettings

STORY_SYSTEM = """You are Hollywood's story architect. Convert a director's brief into a concise,
production-usable film foundation. Return only the requested Pydantic structure. Normalize reusable
world and visual guidance; do not repeat the whole original prompt in every field."""


def story_analysis_prompt(original_prompt: str, settings: GenerationSettings) -> str:
    return f"""Director's brief:\n{original_prompt}\n\nTarget format: {settings.aspect_ratio}.
Preferred visual style: {settings.visual_style}. Approximate final length: {settings.movie_length_seconds}s.
Extract the premise, plot arc, recurring entities, continuity requirements, a world bible, and a visual style bible."""
