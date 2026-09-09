from ...models.schemas import Character, StoryAnalysis

SCENE_SYSTEM = """You are Hollywood's narrative sequence planner. Create broad story scenes rather than
equal-duration clips. Preserve continuity and use supplied character IDs exactly. Return only the requested schema."""


def scene_breakdown_prompt(analysis: StoryAnalysis, characters: list[Character], total_seconds: int) -> str:
    roster = [{"id": character.id, "name": character.name, "role": character.role} for character in characters]
    return f"""Story analysis:\n{analysis.model_dump_json(indent=2)}\n\nRecurring cast:\n{roster}\n\nPlan high-level scenes totaling roughly {total_seconds} seconds."""
