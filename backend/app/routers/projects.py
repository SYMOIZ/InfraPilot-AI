"""Project CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.dependencies import get_project_or_404, get_storage
from app.models.schemas import Project, ProjectCreate, ProjectSummary

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate) -> Project:
    storage = get_storage()
    return storage.create_project(name=body.name, description=body.description)


@router.get("", response_model=list[ProjectSummary])
def list_projects() -> list[ProjectSummary]:
    storage = get_storage()
    return [p.summary() for p in storage.list_projects()]


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    return get_project_or_404(project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str) -> None:
    storage = get_storage()
    if not storage.delete_project(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found",
        )
