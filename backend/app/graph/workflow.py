from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from ..db.repository import ProjectRepository
from ..models.schemas import GenerationSettings, GenerationStatus
from ..services.pipeline_service import MoviePipelineService
from .state import MovieState


@dataclass
class WorkflowRuntime:
    repository: ProjectRepository
    pipeline: MoviePipelineService
    checkpointer: object


class MovieWorkflow:
    STAGES = [
        ("analyze_story", "analyze_story", 0.08, "Analyzing the story"),
        ("extract_characters", "extract_characters", 0.18, "Extracting recurring characters"),
        ("generate_character_references", "generate_character_references", 0.32, "Generating character references"),
        ("break_story_into_scenes", "break_story_into_scenes", 0.42, "Planning narrative scenes"),
        ("break_scenes_into_shots", "break_scenes_into_shots", 0.55, "Designing filmable shots"),
        ("generate_shot_prompts", "generate_shot_prompts", 0.62, "Writing shot prompts"),
        ("generate_keyframes", "generate_keyframes", 0.76, "Generating start and end frames"),
        ("generate_video_clips", "generate_video_clips", 0.9, "Generating video clips"),
        ("validate_clips", "validate_clips", 0.95, "Validating completed clips"),
        ("assemble_movie", "assemble_movie", 1.0, "Assembling movie"),
    ]

    def __init__(self, runtime: WorkflowRuntime) -> None:
        self.runtime = runtime
        self.graph = self._build()

    def _build(self):
        builder = StateGraph(MovieState)
        for index, (name, operation, progress, message) in enumerate(self.STAGES):
            builder.add_node(name, self._node(name, operation, progress, message))
            if index == 0:
                builder.add_edge(START, name)
            else:
                builder.add_edge(self.STAGES[index - 1][0], name)
        builder.add_edge(self.STAGES[-1][0], END)
        return builder.compile(checkpointer=self.runtime.checkpointer)

    def _node(self, stage: str, operation: str, progress: float, message: str):
        async def run(state: MovieState) -> dict:
            project_id = UUID(state["project_id"])
            await self.runtime.pipeline.emit(project_id, stage, progress, message)
            patch = await getattr(self.runtime.pipeline, operation)(state)
            merged = {**state, **patch, "current_stage": stage, "progress": progress, "status": GenerationStatus.RUNNING.value}
            await self.runtime.repository.save_state(project_id, merged)
            await self.runtime.pipeline.emit(project_id, stage, progress, message, **patch)
            settings = GenerationSettings.model_validate(state["generation_settings"])
            if settings.director_mode and stage in {"generate_character_references", "break_story_into_scenes", "break_scenes_into_shots", "generate_keyframes"}:
                interrupt({"stage": stage, "message": f"Director approval required after {stage}."})
            return patch | {"current_stage": stage, "progress": progress, "status": GenerationStatus.RUNNING.value}
        return run

    async def run(self, initial_state: MovieState) -> MovieState:
        config = {"configurable": {"thread_id": initial_state["project_id"]}}
        result = await self.graph.ainvoke(initial_state, config=config)
        if result.get("__interrupt__"):
            paused = {**result, "status": GenerationStatus.WAITING_FOR_APPROVAL.value}
            await self.runtime.repository.save_state(UUID(initial_state["project_id"]), paused)
            await self.runtime.pipeline.emit(UUID(initial_state["project_id"]), paused.get("current_stage", "paused"), paused.get("progress", 0), "Director approval required", GenerationStatus.WAITING_FOR_APPROVAL)
            return paused
        final = {**result, "status": GenerationStatus.COMPLETED.value, "progress": 1.0}
        await self.runtime.repository.save_state(UUID(initial_state["project_id"]), final)
        await self.runtime.pipeline.emit(UUID(initial_state["project_id"]), "complete", 1.0, "Movie pipeline complete", GenerationStatus.COMPLETED)
        return final

    async def resume(self, project_id: UUID) -> MovieState:
        config = {"configurable": {"thread_id": str(project_id)}}
        result = await self.graph.ainvoke(Command(resume={"approved": True}), config=config)
        if result.get("__interrupt__"):
            return {**result, "status": GenerationStatus.WAITING_FOR_APPROVAL.value}
        return {**result, "status": GenerationStatus.COMPLETED.value, "progress": 1.0}
