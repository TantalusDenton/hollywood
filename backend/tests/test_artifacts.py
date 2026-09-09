from uuid import uuid4

from app.services.artifact_service import ArtifactService


def test_movie_manifest_preserves_clip_order(tmp_path):
    service = ArtifactService(tmp_path)
    project_id = uuid4()
    manifest = service.write_manifest(project_id, ["scene-001.mp4", "scene-002.mp4"])
    assert manifest.exists()
    assert manifest.read_text(encoding="utf-8").index("scene-001.mp4") < manifest.read_text(encoding="utf-8").index("scene-002.mp4")
