from ..models.schemas import Character, ContinuityMode, ContinuityPackage, Shot
from .prompts.continuity import continuity_package


class ContinuityService:
    def build(self, shot: Shot, characters: list[Character], previous_end_frame: str | None, mode: ContinuityMode) -> ContinuityPackage:
        return continuity_package(shot, characters, previous_end_frame, mode)
