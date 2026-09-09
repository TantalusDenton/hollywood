from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from ..models.schemas import Artifact, GenerationJob, Project, ProjectDetail
from .models import ArtifactRecord, CharacterRecord, GenerationJobRecord, ProjectRecord, SceneRecord, ShotRecord
from .session import Database


class ProjectNotFoundError(KeyError):
    pass


class ProjectRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def create_project(self, project: Project) -> Project:
        record = ProjectRecord(
            id=str(project.id), title=project.title, original_prompt=project.original_prompt,
            state_json={"generation_settings": project.generation_settings.model_dump(mode="json")},
            current_stage=project.current_stage, progress=project.progress, status=project.status.value,
        )
        async with self.database.session_factory() as session:
            session.add(record)
            await session.commit()
        return project

    async def list_projects(self) -> list[Project]:
        async with self.database.session_factory() as session:
            records = (await session.scalars(select(ProjectRecord).order_by(ProjectRecord.updated_at.desc()))).all()
        return [self._project_from_record(record) for record in records]

    async def get_project(self, project_id: UUID) -> ProjectDetail:
        async with self.database.session_factory() as session:
            record = await session.get(ProjectRecord, str(project_id))
            if not record:
                raise ProjectNotFoundError(str(project_id))
            characters = (await session.scalars(select(CharacterRecord).where(CharacterRecord.project_id == record.id))).all()
            scenes = (await session.scalars(select(SceneRecord).where(SceneRecord.project_id == record.id))).all()
            shots = (await session.scalars(select(ShotRecord).where(ShotRecord.project_id == record.id))).all()
            jobs = (await session.scalars(select(GenerationJobRecord).where(GenerationJobRecord.project_id == record.id))).all()
            artifacts = (await session.scalars(select(ArtifactRecord).where(ArtifactRecord.project_id == record.id))).all()
        payload = record.state_json or {}
        return ProjectDetail(
            **self._project_from_record(record).model_dump(),
            story_analysis=payload.get("story_analysis"),
            characters=[entry.payload for entry in characters], scenes=[entry.payload for entry in scenes],
            shots=[entry.payload for entry in shots], jobs=[self._job_from_record(entry) for entry in jobs],
            artifacts=[self._artifact_from_record(entry) for entry in artifacts], errors=payload.get("errors", []),
        )

    async def save_state(self, project_id: UUID, state: dict) -> None:
        async with self.database.session_factory() as session:
            record = await session.get(ProjectRecord, str(project_id))
            if not record:
                raise ProjectNotFoundError(str(project_id))
            record.title = state.get("title", record.title)
            record.current_stage = state.get("current_stage", record.current_stage)
            record.progress = state.get("progress", record.progress)
            record.status = state.get("status", record.status)
            record.state_json = {
                "generation_settings": state.get("generation_settings", record.state_json.get("generation_settings", {})),
                "story_analysis": state.get("story_analysis"), "errors": state.get("errors", []),
            }
            await self._replace_payloads(session, CharacterRecord, str(project_id), state.get("characters", []), ())
            await self._replace_payloads(session, SceneRecord, str(project_id), state.get("scenes", []), ("sequence_number",))
            await self._replace_payloads(session, ShotRecord, str(project_id), state.get("shots", []), ("scene_id", "sequence_number"))
            record.revision += 1
            await session.commit()

    async def create_job(self, job: GenerationJob) -> None:
        async with self.database.session_factory() as session:
            session.add(GenerationJobRecord(
                id=str(job.id), project_id=str(job.project_id), artifact_type=job.artifact_type.value,
                provider=job.provider, model=job.model, status=job.status.value, progress=job.progress,
                request=job.request, provider_job_id=job.provider_job_id, result=job.result,
                error=job.error, attempt=job.attempt,
            ))
            await session.commit()

    async def save_artifact(self, artifact: Artifact) -> None:
        async with self.database.session_factory() as session:
            session.add(ArtifactRecord(
                id=str(artifact.id), project_id=str(artifact.project_id), type=artifact.type.value,
                path=artifact.path, mime_type=artifact.mime_type, source_id=artifact.source_id,
                prompt=artifact.prompt, metadata_json=artifact.metadata,
            ))
            await session.commit()

    async def _replace_payloads(self, session, model, project_id: str, payloads: list[dict], extra: tuple[str, ...]) -> None:
        records = (await session.scalars(select(model).where(model.project_id == project_id))).all()
        for record in records:
            await session.delete(record)
        for payload in payloads:
            values = {"id": payload["id"], "project_id": project_id, "payload": payload, "status": payload.get("status", "pending")}
            values.update({key: payload[key] for key in extra})
            session.add(model(**values))

    @staticmethod
    def _project_from_record(record: ProjectRecord) -> Project:
        payload = record.state_json or {}
        return Project(
            id=UUID(record.id), title=record.title, original_prompt=record.original_prompt,
            generation_settings=payload.get("generation_settings", {}), current_stage=record.current_stage,
            progress=record.progress, status=record.status, created_at=record.created_at, updated_at=record.updated_at,
        )

    @staticmethod
    def _job_from_record(record: GenerationJobRecord) -> GenerationJob:
        return GenerationJob(id=UUID(record.id), project_id=UUID(record.project_id), artifact_type=record.artifact_type,
                             provider=record.provider, model=record.model, status=record.status, progress=record.progress,
                             request=record.request, provider_job_id=record.provider_job_id, result=record.result,
                             error=record.error, attempt=record.attempt, created_at=record.created_at)

    @staticmethod
    def _artifact_from_record(record: ArtifactRecord) -> Artifact:
        return Artifact(id=UUID(record.id), project_id=UUID(record.project_id), type=record.type, path=record.path,
                        mime_type=record.mime_type, source_id=record.source_id, prompt=record.prompt,
                        metadata=record.metadata_json, created_at=record.created_at)
