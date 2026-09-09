from __future__ import annotations

import asyncio
from pathlib import Path


class FFmpegService:
    async def concatenate(self, clips: list[Path], output: Path) -> Path:
        if not clips:
            raise ValueError("No completed clips are available for assembly.")
        output.parent.mkdir(parents=True, exist_ok=True)
        concat_file = output.with_suffix(".concat.txt")
        concat_file.write_text("".join(f"file '{clip.resolve().as_posix()}'\n" for clip in clips), encoding="utf-8")
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode:
            raise RuntimeError(f"ffmpeg assembly failed: {stderr.decode(errors='replace')[-1000:]}")
        return output
