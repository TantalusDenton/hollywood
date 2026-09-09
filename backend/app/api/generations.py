from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..models.schemas import Character, GenerationStatus
from ..services.dependency_service import DependencyService

router = APIRouter(prefix="/projects/{project_id}", tags=["generations"])


@router.post("/characters/{character_id}/regenerate")
async def regenerate_character(project_id: UUID, character_id: str, request: Request, background_tasks: BackgroundTasks):
    project = await request.app.state.container.repository.get_project(project_id)
    character = next((Character.model_validate(item) for item in project.characters if item.id == character_id), None)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    character.reference_image_path = None
    character.reference_image_metadata = {}
    character.status = GenerationStatus.STALE
    project.characters = [character if item.id == character_id else item for item in project.characters]
    invalidated = DependencyService().invalidate_character(project, character)
    await request.app.state.container.repository.save_state(project_id, invalidated.model_dump(mode="json"))
    background_tasks.add_task(request.app.state.container.run_project, project_id)
    return {"project_id": str(project_id), "character_id": character_id, "status": "queued"}


@router.post("/shots/{shot_id}/regenerate/{target}")
async def regenerate_shot_part(project_id: UUID, shot_id: str, target: str, request: Request, background_tasks: BackgroundTasks):
    if target not in {"prompt", "start_frame", "end_frame", "video"}:
        raise HTTPException(status_code=422, detail="target must be prompt, start_frame, end_frame, or video")
    project = await request.app.state.container.repository.get_project(project_id)
    shot = next((item for item in project.shots if item.id == shot_id), None)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    if target == "prompt":
        shot.generation_prompt = None
        shot.start_frame_path = shot.end_frame_path = shot.video_path = None
    elif target == "start_frame":
        shot.start_frame_path = shot.end_frame_path = shot.video_path = None
    elif target == "end_frame":
        shot.end_frame_path = shot.video_path = None
    else:
        shot.video_path = None
    shot.status = GenerationStatus.STALE
    await request.app.state.container.repository.save_state(project_id, project.model_dump(mode="json"))
    background_tasks.add_task(request.app.state.container.run_project, project_id)
    return {"project_id": str(project_id), "shot_id": shot_id, "target": target, "status": "queued"}
