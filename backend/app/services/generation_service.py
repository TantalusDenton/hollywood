from __future__ import annotations

import asyncio
from pathlib import Path

from ..providers.video.base import GeneratedVideo, VideoProvider


class VideoGenerationService:
    def __init__(self, provider_order: list[str], providers: dict[str, VideoProvider], max_retries: int) -> None:
        self.provider_order = provider_order
        self.providers = providers
        self.max_retries = max_retries

    async def generate_with_fallback(self, **kwargs) -> GeneratedVideo:
        failures: list[Exception] = []
        for name in self.provider_order:
            provider = self.providers.get(name)
            if not provider:
                continue
            try:
                video = await provider.generate_video(**kwargs)
                for _ in range(self.max_retries * 30):
                    status = await provider.get_status(video.job_id)
                    if status.status == "completed":
                        target = kwargs["output_path"]
                        return await provider.download_result(video.job_id, Path(target))
                    if status.status == "failed":
                        raise RuntimeError(f"{name} video job failed")
                    await asyncio.sleep(2)
            except Exception as error:
                failures.append(error)
                # User/content rejections are intentionally not routed to another provider.
                if "content" in str(error).lower() or "safety" in str(error).lower():
                    raise
        raise RuntimeError("All configured video providers failed") from (failures[-1] if failures else None)
