from __future__ import annotations

import asyncio
from pathlib import Path

from .base import GeneratedVideo, VideoProvider, VideoProviderCapabilities


class GoogleVideoProvider(VideoProvider):
    """Official google-genai Veo adapter; provider-specific request shape stays here."""

    def __init__(self, api_key: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for the Google video provider.")
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._operations: dict[str, object] = {}

    def get_capabilities(self) -> VideoProviderCapabilities:
        supports_last_frame = self.model.startswith("veo-3.1")
        return VideoProviderCapabilities(
            text_to_video=True, image_to_video=True, first_frame=True, last_frame=supports_last_frame,
            reference_images=False, audio=True, max_duration_seconds=8,
            supported_resolutions=("720p", "1080p", "4k"), supported_aspect_ratios=("16:9", "9:16"),
        )

    async def generate_video(
        self, *, prompt: str, start_image: Path | None = None, end_image: Path | None = None,
        reference_images: list[Path] | None = None, duration: int | None = None,
        aspect_ratio: str | None = None, resolution: str | None = None, seed: int | None = None,
    ) -> GeneratedVideo:
        from google.genai import types

        capabilities = self.get_capabilities()
        if end_image and not capabilities.last_frame:
            prompt = f"{prompt}\nEnd-state visual target: {end_image.name}."
        config_kwargs = {"number_of_videos": 1, "duration_seconds": min(duration or 8, capabilities.max_duration_seconds)}
        if resolution: config_kwargs["resolution"] = resolution
        if aspect_ratio: config_kwargs["aspect_ratio"] = aspect_ratio
        if end_image and capabilities.last_frame:
            config_kwargs["last_frame"] = types.Image.from_file(location=str(end_image))
        image = types.Image.from_file(location=str(start_image)) if start_image else None
        operation = await asyncio.to_thread(
            self.client.models.generate_videos, model=self.model, prompt=prompt, image=image,
            config=types.GenerateVideosConfig(**config_kwargs),
        )
        job_id = operation.name
        self._operations[job_id] = operation
        return GeneratedVideo(job_id=job_id, provider="google", status="queued", raw={"operation": job_id})

    async def get_status(self, job_id: str) -> GeneratedVideo:
        operation = self._operations.get(job_id)
        if operation is None:
            from google.genai import types
            operation = types.GenerateVideosOperation(name=job_id)
        operation = await asyncio.to_thread(self.client.operations.get, operation)
        self._operations[job_id] = operation
        return GeneratedVideo(job_id=job_id, provider="google", status="completed" if operation.done else "running", progress=1.0 if operation.done else 0.5)

    async def download_result(self, job_id: str, output_path: Path) -> GeneratedVideo:
        operation = self._operations.get(job_id)
        if operation is None or not operation.done:
            raise RuntimeError("Google video operation is not complete.")
        video = operation.response.generated_videos[0].video
        await asyncio.to_thread(self.client.files.download, file=video)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(video.save, str(output_path))
        return GeneratedVideo(job_id=job_id, provider="google", output_path=output_path, status="completed", progress=1.0)

    async def cancel(self, job_id: str) -> None:
        # Veo generate operations currently do not expose a general cancellation endpoint.
        self._operations.pop(job_id, None)
