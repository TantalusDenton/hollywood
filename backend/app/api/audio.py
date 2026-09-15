from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydub.exceptions import CouldntDecodeError

from ..audio_slicer import SUPPORTED_AUDIO_SUFFIXES, slice_audio

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/slice")
async def upload_and_slice_audio(
    request: Request,
    file: UploadFile = File(...),
    slice_seconds: float = Form(default=4, gt=0, le=60),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_AUDIO_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload a WAV or MP3 file.")
    job_id = str(uuid4())
    output_root = request.app.state.container.settings.output_root / "audio" / job_id
    output_root.mkdir(parents=True, exist_ok=True)
    source = output_root / f"source{suffix}"
    try:
        with source.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)
        fragments = await asyncio.to_thread(slice_audio, source, output_root / "slices", slice_seconds)
    except (CouldntDecodeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Hollywood could not read that audio file: {error}") from error
    finally:
        await file.close()
    return {
        "job_id": job_id,
        "slice_seconds": slice_seconds,
        "fragments": [
            {"index": fragment.index, "start_seconds": fragment.start_seconds, "end_seconds": fragment.end_seconds, "url": f"/media/audio/{job_id}/slices/{fragment.path.name}"}
            for fragment in fragments
        ],
    }
