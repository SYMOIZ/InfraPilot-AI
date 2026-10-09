"""Requirements and clarification endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent.requirements_interpreter import RequirementsInterpreter
from app.dependencies import get_project_or_404, get_storage
from app.models.schemas import (
    ClarificationRequest,
    ClarificationResponse,
    Project,
    Requirements,
)
from app.models.validation import validate_requirements

router = APIRouter(prefix="/projects", tags=["requirements"])


@router.put("/{project_id}/requirements", response_model=Project)
def upsert_requirements(project_id: str, body: Requirements) -> Project:
    project = get_project_or_404(project_id)
    ok, errors = validate_requirements(body)
    if not ok:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)
    project.requirements = body
    return get_storage().save_project(project)


@router.post("/{project_id}/clarify", response_model=ClarificationResponse)
def clarify_requirements(project_id: str, body: ClarificationRequest | None = None) -> ClarificationResponse:
    project = get_project_or_404(project_id)
    body = body or ClarificationRequest()
    interpreter = RequirementsInterpreter()

    if body.answers and project.requirements:
        project.clarification_answers.update(body.answers)
        project.requirements = interpreter.apply_answers(
            project.requirements, body.answers
        )
        get_storage().save_project(project)

    questions = interpreter.clarify(
        project.requirements, project.clarification_answers
    )
    message = (
        "No further clarification needed."
        if not questions
        else f"{len(questions)} clarification question(s) suggested."
    )
    return ClarificationResponse(
        project_id=project_id,
        questions=questions,
        message=message,
    )
