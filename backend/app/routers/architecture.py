"""Architecture generation and confirmation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent.architecture_planner import ArchitecturePlanner
from app.dependencies import get_bedrock, get_project_or_404, get_storage
from app.models.schemas import (
    ConfirmArchitectureRequest,
    GenerateRequest,
    Project,
)
from app.models.validation import validate_architecture

router = APIRouter(prefix="/projects", tags=["architecture"])


@router.post("/{project_id}/generate", response_model=Project)
def generate_architecture(
    project_id: str,
    body: GenerateRequest | None = None,
) -> Project:
    project = get_project_or_404(project_id)
    if project.requirements is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requirements must be set before generating architecture",
        )
    body = body or GenerateRequest()
    if project.architecture and not body.regenerate:
        return project

    planner = ArchitecturePlanner(bedrock_client=get_bedrock())
    architecture = planner.generate(
        project.requirements, project.clarification_answers
    )
    ok, errors = validate_architecture(architecture)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Generated architecture failed validation", "errors": errors},
        )
    project.architecture = architecture
    return get_storage().save_project(project)


@router.post("/{project_id}/confirm-architecture", response_model=Project)
def confirm_architecture(
    project_id: str,
    body: ConfirmArchitectureRequest,
) -> Project:
    project = get_project_or_404(project_id)
    ok, errors = validate_architecture(body.architecture)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors,
        )
    architecture = body.architecture
    architecture.confirmed = body.confirmed
    project.architecture = architecture
    return get_storage().save_project(project)
