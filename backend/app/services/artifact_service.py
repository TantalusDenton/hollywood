from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID


class ArtifactService:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    def project_directory(self, project_id: UUID) -> Path:
        path = self.output_root / str(project_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def character_reference_path(self, project_id: UUID, character_id: str) -> Path:
        path = self.project_directory(project_id) / "characters" / character_id
        path.mkdir(parents=True, exist_ok=True)
        return path / "reference.png"

    def shot_path(self, project_id: UUID, scene_id: str, shot_id: str, name: str) -> Path:
        path = self.project_directory(project_id) / "scenes" / scene_id / "shots" / shot_id
        path.mkdir(parents=True, exist_ok=True)
        return path / name

    def write_manifest(self, project_id: UUID, clips: list[str]) -> Path:
        path = self.project_directory(project_id) / "final" / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"clips": clips}, indent=2), encoding="utf-8")
        return path
