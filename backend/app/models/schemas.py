from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GenerationStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STALE = "stale"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class ContinuityMode(StrEnum):
    STRICT = "strict"
    BALANCED = "balanced"
    LOOSE = "loose"


class ArtifactType(StrEnum):
    CHARACTER_REFERENCE = "character_reference"
    START_FRAME = "start_frame"
    END_FRAME = "end_frame"
    VIDEO = "video"
    MANIFEST = "manifest"


class GenerationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visual_style: str = "cinematic realism"
    aspect_ratio: str = "16:9"
    movie_length_seconds: int = Field(default=120, ge=5, le=7200)
    target_shot_length_seconds: int = Field(default=6, ge=2, le=20)
    image_provider: str = "openai"
    video_provider: str = "google"
    image_model: str | None = None
    video_model: str | None = None
    resolution: str = "720p"
    seed: int | None = None
    max_parallel_jobs: int = Field(default=2, ge=1, le=16)
    execution_mode: str = "cloud"
    continuity_mode: ContinuityMode = ContinuityMode.BALANCED
    director_mode: bool = False


class StyleBible(BaseModel):
    visual_style: str
    lens_language: str
    lighting: str
    color_palette: str
    costume_aesthetic: str
    architecture: str
    production_design: str
    camera_movement: str
    aspect_ratio: str
    film_grain: str
    depth_of_field: str


class StoryAnalysis(BaseModel):
    title: str
    premise: str
    synopsis: str
    setting: str
    time_period: str
    genre: list[str]
    tone: list[str]
    major_plot_arc: list[str]
    locations: list[str]
    important_objects: list[str]
    continuity_requirements: list[str]
    recurring_costumes: list[str]
    recurring_environments: list[str]
    world_bible: str
    style_bible: StyleBible


class Character(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    role: str
    category: str = "main"  # main | supporting | background
    age_appearance: str
    species: str = "human"
    gender_presentation: str | None = None
    face: str
    hair: str
    eyes: str
    height: str
    build: str
    clothing: str
    accessories: list[str] = Field(default_factory=list)
    distinguishing_features: list[str] = Field(default_factory=list)
    personality: str
    visual_description: str
    canonical_prompt: str | None = None
    reference_image_path: str | None = None
    reference_image_metadata: dict[str, Any] = Field(default_factory=dict)
    status: GenerationStatus = GenerationStatus.PENDING


class CharacterList(BaseModel):
    characters: list[Character]


class Scene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sequence_number: int
    title: str
    summary: str
    story_purpose: str
    location: str
    time: str
    characters: list[str] = Field(default_factory=list)
    props: list[str] = Field(default_factory=list)
    environment: str
    continuity_in: str | None = None
    continuity_out: str | None = None
    estimated_duration_seconds: int = Field(ge=1)
    status: GenerationStatus = GenerationStatus.PENDING


class SceneList(BaseModel):
    scenes: list[Scene]


class Shot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    scene_id: str
    sequence_number: int
    title: str
    description: str
    duration_seconds: int = Field(ge=2, le=20)
    characters: list[str] = Field(default_factory=list)
    location: str
    props: list[str] = Field(default_factory=list)
    camera: str
    lens: str
    framing: str
    camera_motion: str
    action: str
    beginning_state: str
    ending_state: str
    lighting: str
    environment: str
    visual_style: str
    generation_prompt: str | None = None
    start_frame_prompt: str | None = None
    end_frame_prompt: str | None = None
    start_frame_path: str | None = None
    end_frame_path: str | None = None
    video_path: str | None = None
    status: GenerationStatus = GenerationStatus.PENDING


class ShotList(BaseModel):
    shots: list[Shot]


class ContinuityPackage(BaseModel):
    shot_id: str
    character_references: list[str] = Field(default_factory=list)
    character_descriptions: list[str] = Field(default_factory=list)
    costume_state: str
    location_description: str
    environment: str
    important_props: list[str] = Field(default_factory=list)
    lighting: str
    previous_shot_end_frame: str | None = None
    current_shot_start_frame: str | None = None
    current_shot_end_target: str | None = None
    mode: ContinuityMode = ContinuityMode.BALANCED


class Artifact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    type: ArtifactType
    path: str
    mime_type: str
    source_id: str | None = None
    prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerationJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    artifact_type: ArtifactType
    provider: str
    model: str | None = None
    status: GenerationStatus = GenerationStatus.PENDING
    progress: float = Field(default=0, ge=0, le=1)
    request: dict[str, Any] = Field(default_factory=dict)
    provider_job_id: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] | None = None
    attempt: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ProjectCreate(BaseModel):
    original_prompt: str = Field(min_length=1, max_length=10000)
    generation_settings: GenerationSettings = Field(default_factory=GenerationSettings)


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = "Untitled film"
    original_prompt: str
    synopsis: str | None = None
    generation_settings: GenerationSettings = Field(default_factory=GenerationSettings)
    current_stage: str = "created"
    progress: float = Field(default=0, ge=0, le=1)
    status: GenerationStatus = GenerationStatus.PENDING
    final_movie_path: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectDetail(Project):
    story_analysis: StoryAnalysis | None = None
    characters: list[Character] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    shots: list[Shot] = Field(default_factory=list)
    jobs: list[GenerationJob] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)


class ProjectEvent(BaseModel):
    project_id: UUID
    stage: str
    progress: float
    message: str
    status: GenerationStatus = GenerationStatus.RUNNING
    payload: dict[str, Any] = Field(default_factory=dict)
