from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite import SqliteSaver

from .api import generations_router, projects_router, providers_router
from .config import Settings, get_settings
from .db import Database, ProjectRepository
from .graph import MovieWorkflow, WorkflowRuntime
from .graph.state import MovieState
from .models.schemas import GenerationStatus, ProjectEvent
from .providers.image.openai import OpenAIImageProvider
from .providers.llm.openai import OpenAILLMProvider
from .providers.video.google import GoogleVideoProvider
from .providers.video.wan import WanComfyUIProvider, WanLocalProvider, WanRestProvider
from .services.artifact_service import ArtifactService
from .services.event_service import ProjectEventBus
from .services.pipeline_service import MoviePipelineService


class HollywoodContainer:
    def __init__(self, settings: Settings, database: Database, checkpointer: SqliteSaver) -> None:
        self.settings = settings
        self.database = database
        self.repository = ProjectRepository(database)
        self.events = ProjectEventBus()
        self.checkpointer = checkpointer

    def _pipeline(self) -> MoviePipelineService:
        """Create providers only when a generation is requested, so browsing projects needs no API keys."""
        llm = OpenAILLMProvider(self.settings.openai_api_key, self.settings.openai_llm_model)
        image = OpenAIImageProvider(self.settings.openai_api_key, self.settings.openai_image_model)
        providers = {}
        if self.settings.google_api_key:
            providers["google"] = GoogleVideoProvider(self.settings.google_api_key, self.settings.google_video_model)
        if self.settings.wan_api_url:
            providers["wan_remote"] = WanComfyUIProvider(self.settings.wan_api_url, self.settings.wan_api_key, self.settings.wan_model) if self.settings.wan_backend == "comfyui" else WanRestProvider(self.settings.wan_api_url, self.settings.wan_api_key, self.settings.wan_model)
        if self.settings.wan_local_url:
            providers["wan_local"] = WanLocalProvider(self.settings.wan_local_url, None, self.settings.wan_model)
        return MoviePipelineService(
            settings=self.settings, llm=llm, image_provider=image, video_providers=providers,
            artifacts=ArtifactService(self.settings.output_root), events=self.events,
        )

    def provider_capabilities(self) -> dict:
        return {
            "image": {"openai": {"configured": bool(self.settings.openai_api_key), "model": self.settings.openai_image_model}},
            "video": {"google": {"configured": bool(self.settings.google_api_key), "model": self.settings.google_video_model, "capabilities": {"first_frame": True, "last_frame": self.settings.google_video_model.startswith("veo-3.1"), "audio": True}}, "wan": {"configured": bool(self.settings.wan_api_url or self.settings.wan_local_url), "backend": self.settings.wan_backend, "mode": self.settings.wan_mode}},
        }

    async def run_project(self, project_id: UUID, resume: bool = False) -> None:
        detail = await self.repository.get_project(project_id)
        state: MovieState = {
            "project_id": str(detail.id), "original_prompt": detail.original_prompt,
            "generation_settings": detail.generation_settings.model_dump(mode="json"), "current_stage": detail.current_stage,
            "progress": detail.progress, "status": GenerationStatus.RUNNING.value, "errors": detail.errors,
        }
        for key in ("title", "story_analysis", "characters", "scenes", "shots", "final_movie_path"):
            value = getattr(detail, key, None)
            if value:
                state[key] = [item.model_dump(mode="json") for item in value] if key in {"characters", "scenes", "shots"} else (value.model_dump(mode="json") if key == "story_analysis" else value)
        try:
            workflow = MovieWorkflow(WorkflowRuntime(repository=self.repository, pipeline=self._pipeline(), checkpointer=self.checkpointer))
            if resume:
                result = await workflow.resume(project_id)
                await self.repository.save_state(project_id, result)
            else:
                await workflow.run(state)
        except Exception as error:
            failed = {**state, "status": GenerationStatus.FAILED.value, "errors": [*state.get("errors", []), {"type": type(error).__name__, "message": str(error)}]}
            await self.repository.save_state(project_id, failed)
            await self.events.publish(ProjectEvent(project_id=project_id, stage=state.get("current_stage", "created"), progress=state.get("progress", 0), message=str(error), status=GenerationStatus.FAILED))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.output_root.mkdir(parents=True, exist_ok=True)
    settings.checkpoint_database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.checkpoint_database_path, check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    checkpointer.setup()
    database = Database(settings.database_url)
    await database.create_schema()
    app.state.container = HollywoodContainer(settings, database, checkpointer)
    yield
    await database.close()
    connection.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Hollywood API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.include_router(projects_router, prefix=settings.api_prefix)
    app.include_router(generations_router, prefix=settings.api_prefix)
    app.include_router(providers_router, prefix=settings.api_prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "hollywood"}

    return app


app = create_app()
