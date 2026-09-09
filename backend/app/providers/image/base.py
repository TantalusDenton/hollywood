from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ImageProviderCapabilities:
    reference_images: bool
    seed: bool
    supported_aspect_ratios: tuple[str, ...] = ("1:1", "16:9", "9:16")


@dataclass(frozen=True)
class GeneratedImage:
    path: Path
    prompt: str
    model: str
    metadata: dict = field(default_factory=dict)


class ImageProvider(ABC):
    @abstractmethod
    def get_capabilities(self) -> ImageProviderCapabilities: ...

    @abstractmethod
    async def generate_image(
        self, *, prompt: str, output_path: Path, reference_images: list[Path] | None = None,
        aspect_ratio: str | None = None, resolution: str | None = None, seed: int | None = None,
    ) -> GeneratedImage: ...
