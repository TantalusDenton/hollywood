from __future__ import annotations

from ..models.schemas import Character, GenerationStatus, ProjectDetail


class DependencyService:
    """Marks only descendants of an edited artifact stale; successful unrelated work is retained."""

    def invalidate_character(self, project: ProjectDetail, character: Character) -> ProjectDetail:
        for shot in project.shots:
            if character.id in shot.characters:
                shot.status = GenerationStatus.STALE
                shot.start_frame_path = None
                shot.end_frame_path = None
                shot.video_path = None
        return project

    def invalidate_end_frame(self, project: ProjectDetail, shot_id: str) -> ProjectDetail:
        for shot in project.shots:
            if shot.id == shot_id:
                shot.video_path = None
                shot.status = GenerationStatus.STALE
        return project
