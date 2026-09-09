from __future__ import annotations

import base64
from pathlib import Path

from openai import AsyncOpenAI

from .base import GeneratedImage, ImageProvider, ImageProviderCapabilities


class OpenAIImageProvider(ImageProvider):
    """Uses generate for text-only requests and edit for canonical-image conditioning."""

    def __init__(self, api_key: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI image provider.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def get_capabilities(self) -> ImageProviderCapabilities:
        return ImageProviderCapabilities(reference_images=True, seed=False)

    async def generate_image(
        self, *, prompt: str, output_path: Path, reference_images: list[Path] | None = None,
        aspect_ratio: str | None = None, resolution: str | None = None, seed: int | None = None,
    ) -> GeneratedImage:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        size = {"16:9": "1536x1024", "9:16": "1024x1536"}.get(aspect_ratio or "", "1024x1024")
        if reference_images:
            files = [path.open("rb") for path in reference_images]
            try:
                response = await self.client.images.edit(model=self.model, image=files, prompt=prompt, size=size)
            finally:
                for file in files:
                    file.close()
        else:
            response = await self.client.images.generate(model=self.model, prompt=prompt, size=size)
        image = response.data[0]
        if not image.b64_json:
            raise RuntimeError("Image provider returned no base64 image payload.")
        output_path.write_bytes(base64.b64decode(image.b64_json))
        return GeneratedImage(path=output_path, prompt=prompt, model=self.model, metadata={"size": size})
