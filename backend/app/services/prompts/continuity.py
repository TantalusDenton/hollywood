from ...models.schemas import Character, ContinuityMode, ContinuityPackage, Shot


def continuity_package(shot: Shot, characters: list[Character], previous_end_frame: str | None, mode: ContinuityMode) -> ContinuityPackage:
    cast = [character for character in characters if character.id in shot.characters]
    return ContinuityPackage(
        shot_id=shot.id, character_references=[item.reference_image_path for item in cast if item.reference_image_path],
        character_descriptions=[item.visual_description for item in cast], costume_state="; ".join(item.clothing for item in cast),
        location_description=shot.location, environment=shot.environment, important_props=shot.props,
        lighting=shot.lighting, previous_shot_end_frame=previous_end_frame, current_shot_start_frame=shot.start_frame_path,
        current_shot_end_target=shot.end_frame_path, mode=mode,
    )
