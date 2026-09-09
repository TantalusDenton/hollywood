from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from urllib.parse import urljoin

import httpx

from .base import WanVideoProvider
from ..base import GeneratedVideo


class WanRestProvider(WanVideoProvider):
    """Adapter contract for a remote WAN-compatible HTTP API. Configure its endpoint per vendor."""

    def __init__(self, url: str, api_key: str | None, model: str | None) -> None:
        self.url, self.api_key, self.model = url.rstrip("/"), api_key, model
        self.client = httpx.AsyncClient(timeout=120)

    async def submit_normalized_request(self, payload: dict) -> dict:
        response = await self.client.post(f"{self.url}/generate", json=payload, headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})
        response.raise_for_status()
        return response.json()

    async def generate_video(
        self, *, prompt: str, start_image: Path | None = None, end_image: Path | None = None,
        reference_images: list[Path] | None = None, duration: int | None = None,
        aspect_ratio: str | None = None, resolution: str | None = None, seed: int | None = None,
    ) -> GeneratedVideo:
        data = {"prompt": prompt, "duration": str(duration or 6), "aspect_ratio": aspect_ratio or "16:9", "resolution": resolution or "720p"}
        if self.model:
            data["model"] = self.model
        if seed is not None:
            data["seed"] = str(seed)
        handles = []
        files = []
        try:
            for field, path in [("start_image", start_image), ("end_image", end_image)]:
                if path:
                    handle = path.open("rb")
                    handles.append(handle)
                    files.append((field, (path.name, handle, "image/png")))
            for index, path in enumerate(reference_images or []):
                handle = path.open("rb")
                handles.append(handle)
                files.append((f"reference_images[{index}]", (path.name, handle, "image/png")))
            response = await self.client.post(f"{self.url}/generate", data=data, files=files or None, headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})
            response.raise_for_status()
            payload = response.json()
        finally:
            for handle in handles:
                handle.close()
        job_id = payload.get("job_id")
        if not job_id:
            raise RuntimeError("WAN endpoint returned no job_id.")
        return GeneratedVideo(job_id=job_id, provider="wan", status=payload.get("status", "queued"), progress=payload.get("progress", 0), raw=payload)

    async def get_status(self, job_id: str) -> GeneratedVideo:
        response = await self.client.get(f"{self.url}/jobs/{job_id}", headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})
        response.raise_for_status()
        payload = response.json()
        return GeneratedVideo(job_id=job_id, provider="wan", status=payload.get("status", "running"), progress=payload.get("progress", 0), raw=payload)

    async def download_result(self, job_id: str, output_path: Path) -> GeneratedVideo:
        status = await self.get_status(job_id)
        source = (status.raw or {}).get("output")
        if not source:
            raise RuntimeError("WAN job completed without an output location.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if Path(source).exists():
            await asyncio.to_thread(shutil.copyfile, source, output_path)
        else:
            response = await self.client.get(urljoin(f"{self.url}/", source))
            response.raise_for_status()
            output_path.write_bytes(response.content)
        return GeneratedVideo(job_id=job_id, provider="wan", output_path=output_path, status="completed", progress=1.0, raw=status.raw)

    async def cancel(self, job_id: str) -> None:
        response = await self.client.delete(f"{self.url}/jobs/{job_id}", headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})
        if response.status_code not in {200, 202, 204, 404}:
            response.raise_for_status()
