from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

from ..config import Settings
from ..models.schemas import (
    Artifact, ArtifactType, Character, CharacterList, GenerationSettings, GenerationStatus,
    ProjectEvent, Scene, SceneList, Shot, ShotList, StoryAnalysis,
)
from ..providers.image.base import ImageProvider
from ..providers.llm.base import LLMProvider
from ..providers.video.base import VideoProvider
from .artifact_service import ArtifactService
from .continuity_service import ContinuityService
from .event_service import ProjectEventBus
from .ffmpeg_service import FFmpegService
from .prompts.characters import CHARACTER_SYSTEM, character_extraction_prompt, character_reference_prompt
from .prompts.keyframes import end_frame_prompt, start_frame_prompt
from .prompts.scenes import SCENE_SYSTEM, scene_breakdown_prompt
from .prompts.shots import SHOT_SYSTEM, shot_breakdown_prompt, video_prompt
from .prompts.story import STORY_SYSTEM, story_analysis_prompt


class MoviePipelineService:
    """Idempotent pipeline operations. Each operation returns serializable state patches."""

    def __init__(
        self, *, settings: Settings, llm: LLMProvider, image_provider: ImageProvider,
        video_providers: dict[str, VideoProvider], artifacts: ArtifactService, events: ProjectEventBus,
    ) -> None:
        self.settings = settings
        self.llm = llm
        self.image_provider = image_provider
        self.video_providers = video_providers
        self.artifacts = artifacts
        self.events = events
        self.continuity = ContinuityService()
        self.ffmpeg = FFmpegService()

    async def emit(self, project_id: UUID, stage: str, progress: float, message: str, status: GenerationStatus = GenerationStatus.RUNNING, **payload) -> None:
        await self.events.publish(ProjectEvent(project_id=project_id, stage=stage, progress=progress, message=message, status=status, payload=payload))

    async def analyze_story(self, state: dict) -> dict:
        if state.get("story_analysis"):
            return {}
        settings = GenerationSettings.model_validate(state["generation_settings"])
        analysis = await self.llm.generate_structured(
            system=STORY_SYSTEM, user=story_analysis_prompt(state["original_prompt"], settings), schema=StoryAnalysis,
        )
        return {"title": analysis.title, "story_analysis": analysis.model_dump(mode="json")}

    async def extract_characters(self, state: dict) -> dict:
        if state.get("characters"):
            return {}
        analysis = StoryAnalysis.model_validate(state["story_analysis"])
        result = await self.llm.generate_structured(system=CHARACTER_SYSTEM, user=character_extraction_prompt(analysis), schema=CharacterList)
        characters = []
        for character in result.characters:
            character.canonical_prompt = character_reference_prompt(character, analysis)
            characters.append(character.model_dump(mode="json"))
        return {"characters": characters}

    async def generate_character_references(self, state: dict) -> dict:
        project_id = UUID(state["project_id"])
        analysis = StoryAnalysis.model_validate(state["story_analysis"])
        characters = [Character.model_validate(item) for item in state.get("characters", [])]
        semaphore = asyncio.Semaphore(self.settings.max_parallel_image_jobs)

        async def generate(character: Character) -> Character:
            if character.reference_image_path and Path(character.reference_image_path).exists():
                return character
            async with semaphore:
                await self.emit(project_id, "generate_character_references", state.get("progress", 0), f"Generating {character.name}")
                path = self.artifacts.character_reference_path(project_id, character.id)
                image = await self.image_provider.generate_image(
                    prompt=character.canonical_prompt or character_reference_prompt(character, analysis), output_path=path,
                    aspect_ratio=analysis.style_bible.aspect_ratio,
                )
                character.reference_image_path = str(image.path)
                character.reference_image_metadata = image.metadata | {"model": image.model, "prompt": image.prompt}
                character.status = GenerationStatus.COMPLETED
                return character

        generated = await asyncio.gather(*(generate(item) for item in characters))
        return {"characters": [item.model_dump(mode="json") for item in generated]}

    async def break_story_into_scenes(self, state: dict) -> dict:
        if state.get("scenes"):
            return {}
        analysis = StoryAnalysis.model_validate(state["story_analysis"])
        characters = [Character.model_validate(item) for item in state.get("characters", [])]
        settings = GenerationSettings.model_validate(state["generation_settings"])
        result = await self.llm.generate_structured(
            system=SCENE_SYSTEM, user=scene_breakdown_prompt(analysis, characters, settings.movie_length_seconds), schema=SceneList,
        )
        return {"scenes": [scene.model_dump(mode="json") for scene in sorted(result.scenes, key=lambda item: item.sequence_number)]}

    async def break_scenes_into_shots(self, state: dict) -> dict:
        if state.get("shots"):
            return {}
        analysis = StoryAnalysis.model_validate(state["story_analysis"])
        characters = [Character.model_validate(item) for item in state.get("characters", [])]
        scenes = [Scene.model_validate(item) for item in state.get("scenes", [])]
        settings = GenerationSettings.model_validate(state["generation_settings"])

        async def plan(scene: Scene) -> list[Shot]:
            result = await self.llm.generate_structured(
                system=SHOT_SYSTEM, user=shot_breakdown_prompt(scene, characters, analysis, settings.target_shot_length_seconds), schema=ShotList,
            )
            for shot in result.shots:
                shot.scene_id = scene.id
            return result.shots

        planned = await asyncio.gather(*(plan(scene) for scene in scenes))
        return {"shots": [shot.model_dump(mode="json") for group in planned for shot in sorted(group, key=lambda item: item.sequence_number)]}

    async def generate_shot_prompts(self, state: dict) -> dict:
        analysis = StoryAnalysis.model_validate(state["story_analysis"])
        characters = [Character.model_validate(item) for item in state.get("characters", [])]
        shots = [Shot.model_validate(item) for item in state.get("shots", [])]
        for shot in shots:
            if not shot.generation_prompt:
                cast = [character.visual_description for character in characters if character.id in shot.characters]
                shot.generation_prompt = video_prompt(shot, analysis, cast)
        return {"shots": [shot.model_dump(mode="json") for shot in shots]}

    async def generate_keyframes(self, state: dict) -> dict:
        project_id = UUID(state["project_id"])
        analysis = StoryAnalysis.model_validate(state["story_analysis"])
        settings = GenerationSettings.model_validate(state["generation_settings"])
        characters = [Character.model_validate(item) for item in state.get("characters", [])]
        shots = [Shot.model_validate(item) for item in state.get("shots", [])]
        previous_end: str | None = None
        for shot in shots:
            continuity = self.continuity.build(shot, characters, previous_end, settings.continuity_mode)
            refs = [Path(path) for path in continuity.character_references]
            if not shot.start_frame_path:
                shot.start_frame_prompt = start_frame_prompt(shot, analysis, continuity)
                start = await self.image_provider.generate_image(
                    prompt=shot.start_frame_prompt, output_path=self.artifacts.shot_path(project_id, shot.scene_id, shot.id, "start.png"),
                    reference_images=refs, aspect_ratio=settings.aspect_ratio, resolution=settings.resolution, seed=settings.seed,
                )
                shot.start_frame_path = str(start.path)
            continuity.current_shot_start_frame = shot.start_frame_path
            if not shot.end_frame_path:
                shot.end_frame_prompt = end_frame_prompt(shot, analysis, continuity)
                end_refs = [Path(shot.start_frame_path), *refs]
                end = await self.image_provider.generate_image(
                    prompt=shot.end_frame_prompt, output_path=self.artifacts.shot_path(project_id, shot.scene_id, shot.id, "end.png"),
                    reference_images=end_refs, aspect_ratio=settings.aspect_ratio, resolution=settings.resolution, seed=settings.seed,
                )
                shot.end_frame_path = str(end.path)
            shot.status = GenerationStatus.COMPLETED
            previous_end = shot.end_frame_path
        return {"shots": [shot.model_dump(mode="json") for shot in shots]}

    async def generate_video_clips(self, state: dict) -> dict:
        project_id = UUID(state["project_id"])
        settings = GenerationSettings.model_validate(state["generation_settings"])
        provider_names = list(dict.fromkeys([settings.video_provider, *self.settings.video_provider_order]))
        if not any(name in self.video_providers for name in provider_names):
            raise RuntimeError(f"Video provider '{settings.video_provider}' is not configured.")
        shots = [Shot.model_validate(item) for item in state.get("shots", [])]
        semaphore = asyncio.Semaphore(self.settings.max_parallel_video_jobs)

        async def generate(shot: Shot) -> Shot:
            if shot.video_path and Path(shot.video_path).exists():
                return shot
            async with semaphore:
                if not shot.start_frame_path:
                    raise RuntimeError(f"Shot {shot.id} has no start frame.")
                output = self.artifacts.shot_path(project_id, shot.scene_id, shot.id, "output.mp4")
                failures: list[Exception] = []
                for provider_name in provider_names:
                    provider = self.video_providers.get(provider_name)
                    if not provider:
                        continue
                    try:
                        capabilities = provider.get_capabilities()
                        job = await provider.generate_video(
                            prompt=shot.generation_prompt or shot.description, start_image=Path(shot.start_frame_path),
                            end_image=Path(shot.end_frame_path) if shot.end_frame_path and capabilities.last_frame else None,
                            reference_images=None, duration=shot.duration_seconds, aspect_ratio=settings.aspect_ratio,
                            resolution=settings.resolution, seed=settings.seed,
                        )
                        for _ in range(self.settings.max_generation_retries * 60):
                            status = await provider.get_status(job.job_id)
                            if status.status == "completed":
                                result = await provider.download_result(job.job_id, output)
                                shot.video_path = str(result.output_path)
                                shot.status = GenerationStatus.COMPLETED
                                return shot
                            if status.status == "failed":
                                raise RuntimeError(f"{provider_name} rejected the video job")
                            await asyncio.sleep(2)
                        raise TimeoutError(f"{provider_name} video job for shot {shot.id} did not complete in time.")
                    except Exception as error:
                        failures.append(error)
                        # Policy/content errors need director intervention rather than an automatic provider change.
                        if "content" in str(error).lower() or "safety" in str(error).lower() or "rejected" in str(error).lower():
                            raise
                raise RuntimeError(f"All configured video providers failed for shot {shot.id}") from (failures[-1] if failures else None)

        generated = await asyncio.gather(*(generate(shot) for shot in shots))
        return {"shots": [shot.model_dump(mode="json") for shot in generated]}

    async def validate_clips(self, state: dict) -> dict:
        missing = [item.id for item in (Shot.model_validate(shot) for shot in state.get("shots", [])) if not item.video_path or not Path(item.video_path).exists()]
        if missing:
            raise RuntimeError(f"Missing completed video artifacts for shots: {', '.join(missing)}")
        return {}

    async def assemble_movie(self, state: dict) -> dict:
        project_id = UUID(state["project_id"])
        shots = [Shot.model_validate(item) for item in state.get("shots", [])]
        clips = [Path(shot.video_path) for shot in sorted(shots, key=lambda item: (item.scene_id, item.sequence_number)) if shot.video_path]
        manifest = self.artifacts.write_manifest(project_id, [str(path) for path in clips])
        output = self.artifacts.project_directory(project_id) / "final" / "movie.mp4"
        movie = await self.ffmpeg.concatenate(clips, output)
        return {"final_movie_path": str(movie), "manifest_path": str(manifest)}
