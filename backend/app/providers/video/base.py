from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoProviderCapabilities:
    text_to_video: bool
    image_to_video: bool
    first_frame: bool
    last_frame: bool
    reference_images: bool
    audio: bool
    max_duration_seconds: int
    supported_resolutions: tuple[str, ...]
    supported_aspect_ratios: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedVideo:
    job_id: str
    provider: str
    output_path: Path | None = None
    status: str = "queued"
    progress: float = 0.0
    raw: dict | None = None


class VideoProvider(ABC):
    @abstractmethod
    def get_capabilities(self) -> VideoProviderCapabilities: ...

    @abstractmethod
    async def generate_video(
        self, *, prompt: str, start_image: Path | None = None, end_image: Path | None = None,
        reference_images: list[Path] | None = None, duration: int | None = None,
        aspect_ratio: str | None = None, resolution: str | None = None, seed: int | None = None,
    ) -> GeneratedVideo: ...

    @abstractmethod
    async def get_status(self, job_id: str) -> GeneratedVideo: ...

    @abstractmethod
    async def download_result(self, job_id: str, output_path: Path) -> GeneratedVideo: ...

    @abstractmethod
    async def cancel(self, job_id: str) -> None: ...
