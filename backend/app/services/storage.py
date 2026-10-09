"""Project and file storage: DynamoDB/S3 when configured, else local JSON/files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from app.config import Settings, get_settings
from app.models.schemas import Project


class StorageService:
    """Unified storage with cloud backends and local fallbacks."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.data_dir = self.settings.local_data_path
        self.projects_dir = self.data_dir / "projects"
        self.files_dir = self.data_dir / "files"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self._memory: Dict[str, Project] = {}
        # Cloud storage is independent of DEMO_MODE (which only mocks Bedrock).
        self._use_dynamo = (
            bool(self.settings.dynamodb_table) and not self.settings.force_local_storage
        )
        self._use_s3 = (
            bool(self.settings.s3_bucket) and not self.settings.force_local_storage
        )
        self._dynamo = None
        self._s3 = None
        if self._use_dynamo:
            try:
                import boto3

                self._dynamo = boto3.resource(
                    "dynamodb", region_name=self.settings.aws_region
                ).Table(self.settings.dynamodb_table)
            except Exception:
                self._use_dynamo = False
        if self._use_s3:
            try:
                import boto3

                self._s3 = boto3.client("s3", region_name=self.settings.aws_region)
            except Exception:
                self._use_s3 = False

    def _project_path(self, project_id: str) -> Path:
        return self.projects_dir / f"{project_id}.json"

    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        project = Project(name=name, description=description)
        self.save_project(project)
        return project

    def save_project(self, project: Project) -> Project:
        project.touch()
        payload = project.model_dump(mode="json", by_alias=True)
        self._memory[project.id] = project
        if self._use_dynamo and self._dynamo is not None:
            try:
                # Store as JSON string to avoid float/Decimal edge cases
                self._dynamo.put_item(
                    Item={
                        "id": project.id,
                        "data_json": json.dumps(payload, default=str),
                        "name": project.name,
                        "updated_at": str(getattr(project, "updated_at", "") or ""),
                    }
                )
                return project
            except Exception:
                pass
        path = self._project_path(project.id)
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        if project_id in self._memory:
            return self._memory[project_id]
        if self._use_dynamo and self._dynamo is not None:
            try:
                resp = self._dynamo.get_item(Key={"id": project_id})
                item = resp.get("Item")
                if item:
                    if "data_json" in item:
                        project = Project.model_validate(json.loads(item["data_json"]))
                        self._memory[project_id] = project
                        return project
                    if "data" in item:
                        project = Project.model_validate(item["data"])
                        self._memory[project_id] = project
                        return project
            except Exception:
                pass
        path = self._project_path(project_id)
        if path.exists():
            project = Project.model_validate(json.loads(path.read_text(encoding="utf-8")))
            self._memory[project_id] = project
            return project
        return None

    def list_projects(self) -> List[Project]:
        projects: Dict[str, Project] = dict(self._memory)
        if self._use_dynamo and self._dynamo is not None:
            try:
                resp = self._dynamo.scan()
                for item in resp.get("Items", []):
                    if "data_json" in item:
                        p = Project.model_validate(json.loads(item["data_json"]))
                        projects[p.id] = p
                    elif item.get("data"):
                        p = Project.model_validate(item["data"])
                        projects[p.id] = p
            except Exception:
                pass
        for path in self.projects_dir.glob("*.json"):
            try:
                p = Project.model_validate(json.loads(path.read_text(encoding="utf-8")))
                projects.setdefault(p.id, p)
            except Exception:
                continue
        return sorted(projects.values(), key=lambda p: p.updated_at, reverse=True)

    def delete_project(self, project_id: str) -> bool:
        existed = self.get_project(project_id) is not None
        self._memory.pop(project_id, None)
        path = self._project_path(project_id)
        if path.exists():
            path.unlink()
            existed = True
        # Remove uploaded files
        proj_files = self.files_dir / project_id
        if proj_files.exists():
            shutil.rmtree(proj_files, ignore_errors=True)
        if self._use_dynamo and self._dynamo is not None:
            try:
                self._dynamo.delete_item(Key={"id": project_id})
            except Exception:
                pass
        return existed

    def save_upload(
        self,
        project_id: str,
        filename: str,
        content: bytes,
    ) -> str:
        """Save uploaded file; returns storage key/path."""
        safe_name = Path(filename).name
        key = f"{project_id}/{uuid4().hex}_{safe_name}"
        if self._use_s3 and self._s3 is not None:
            try:
                self._s3.put_object(
                    Bucket=self.settings.s3_bucket,
                    Key=key,
                    Body=content,
                )
                return f"s3://{self.settings.s3_bucket}/{key}"
            except Exception:
                pass
        dest_dir = self.files_dir / project_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{uuid4().hex}_{safe_name}"
        dest.write_bytes(content)
        return str(dest)

    def read_upload(self, location: str) -> bytes:
        if location.startswith("s3://") and self._s3 is not None:
            # s3://bucket/key
            without = location[5:]
            bucket, _, key = without.partition("/")
            resp = self._s3.get_object(Bucket=bucket, Key=key)
            return resp["Body"].read()
        return Path(location).read_bytes()

    def clear_all(self) -> None:
        """Test helper: wipe in-memory and local project data."""
        self._memory.clear()
        for path in self.projects_dir.glob("*.json"):
            path.unlink(missing_ok=True)
