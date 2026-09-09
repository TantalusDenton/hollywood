from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..db.repository import ProjectNotFoundError
from ..models.schemas import GenerationStatus, Project, ProjectCreate

router = APIRouter(prefix="/projects", tags=["projects"])


def container(request: Request):
    return request.app.state.container


@router.post("", response_model=Project, status_code=201)
async def create_project(payload: ProjectCreate, request: Request, background_tasks: BackgroundTasks) -> Project:
    project = Project(original_prompt=payload.original_prompt, generation_settings=payload.generation_settings)
    app_container = container(request)
    await app_container.repository.create_project(project)
    background_tasks.add_task(app_container.run_project, project.id)
    return project


@router.get("", response_model=list[Project])
async def list_projects(request: Request) -> list[Project]:
    return await container(request).repository.list_projects()


@router.get("/{project_id}")
async def get_project(project_id: UUID, request: Request):
    try:
        return await container(request).repository.get_project(project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error


@router.post("/{project_id}/run")
async def run_project(project_id: UUID, request: Request, background_tasks: BackgroundTasks):
    try:
        await container(request).repository.get_project(project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error
    background_tasks.add_task(container(request).run_project, project_id)
    return {"project_id": str(project_id), "status": "queued"}


@router.post("/{project_id}/resume")
async def resume_project(project_id: UUID, request: Request, background_tasks: BackgroundTasks):
    try:
        await container(request).repository.get_project(project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error
    background_tasks.add_task(container(request).run_project, project_id, True)
    return {"project_id": str(project_id), "status": "resuming"}


@router.get("/{project_id}/events")
async def stream_project_events(project_id: UUID, request: Request) -> StreamingResponse:
    app_container = container(request)
    queue = app_container.events.subscribe(project_id)

    async def stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"event: pipeline\ndata: {event.model_dump_json()}\n\n"
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            app_container.events.unsubscribe(project_id, queue)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/{project_id}/cancel")
async def cancel_project(project_id: UUID, request: Request):
    # Cancellation of cloud jobs is delegated to the provider boundary; this marks the project terminal locally.
    detail = await container(request).repository.get_project(project_id)
    state = detail.model_dump(mode="json")
    state["status"] = GenerationStatus.CANCELLED.value
    state["current_stage"] = "cancelled"
    await container(request).repository.save_state(project_id, state)
    return {"project_id": str(project_id), "status": "cancelled"}
