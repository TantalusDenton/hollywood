"""Audio slicing service used by the Hollywood upload API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydub import AudioSegment


SUPPORTED_AUDIO_SUFFIXES = {".mp3", ".wav"}


@dataclass(frozen=True)
class AudioSlice:
    index: int
    start_seconds: float
    end_seconds: float
    path: Path


def slice_audio(input_path: Path, output_dir: Path, fragment_length_seconds: float = 4) -> list[AudioSlice]:
    """Split a WAV or MP3 into numbered MP3 cues and return their timeline metadata."""
    if input_path.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
        raise ValueError("Only WAV and MP3 files are supported.")
    if fragment_length_seconds <= 0:
        raise ValueError("Slice length must be greater than zero.")

    output_dir.mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(input_path)
    fragment_ms = round(fragment_length_seconds * 1000)
    slices: list[AudioSlice] = []
    for index, start_ms in enumerate(range(0, len(audio), fragment_ms), start=1):
        end_ms = min(start_ms + fragment_ms, len(audio))
        output_path = output_dir / f"shot_{index:02d}.mp3"
        audio[start_ms:end_ms].export(output_path, format="mp3", bitrate="320k")
        slices.append(AudioSlice(index=index, start_seconds=start_ms / 1000, end_seconds=end_ms / 1000, path=output_path))
    return slices
