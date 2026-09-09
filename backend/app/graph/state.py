from typing import NotRequired, TypedDict


class MovieState(TypedDict):
    project_id: str
    original_prompt: str
    generation_settings: dict
    current_stage: str
    progress: float
    status: str
    title: NotRequired[str]
    story_analysis: NotRequired[dict]
    characters: NotRequired[list[dict]]
    scenes: NotRequired[list[dict]]
    shots: NotRequired[list[dict]]
    final_movie_path: NotRequired[str]
    manifest_path: NotRequired[str]
    errors: NotRequired[list[dict]]
