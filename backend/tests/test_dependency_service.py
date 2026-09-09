from uuid import uuid4

from app.models.schemas import Character, GenerationSettings, ProjectDetail, Shot
from app.services.dependency_service import DependencyService


def character() -> Character:
    return Character(name="Mara", role="Lead", age_appearance="30s", face="angular", hair="black", eyes="brown", height="tall", build="lean", clothing="tan jacket", personality="curious", visual_description="A tall archaeologist")


def shot(character_id: str) -> Shot:
    return Shot(scene_id="scene-1", sequence_number=1, title="Arrival", description="Arrival", duration_seconds=6, characters=[character_id], location="ruins", camera="A cam", lens="35mm", framing="wide", camera_motion="dolly", action="walks", beginning_state="outside", ending_state="inside", lighting="blue", environment="desert", visual_style="cinematic", start_frame_path="start.png", end_frame_path="end.png", video_path="clip.mp4")


def test_character_edit_marks_only_affected_shots_stale():
    recurring = character()
    project = ProjectDetail(id=uuid4(), original_prompt="story", generation_settings=GenerationSettings(), characters=[recurring], shots=[shot(recurring.id)])
    updated = DependencyService().invalidate_character(project, recurring)
    assert updated.shots[0].status == "stale"
    assert updated.shots[0].start_frame_path is None
    assert updated.shots[0].video_path is None


def test_end_frame_edit_only_invalidates_video():
    recurring = character()
    planned = shot(recurring.id)
    project = ProjectDetail(id=uuid4(), original_prompt="story", generation_settings=GenerationSettings(), characters=[recurring], shots=[planned])
    updated = DependencyService().invalidate_end_frame(project, planned.id)
    assert updated.shots[0].start_frame_path == "start.png"
    assert updated.shots[0].end_frame_path == "end.png"
    assert updated.shots[0].video_path is None
