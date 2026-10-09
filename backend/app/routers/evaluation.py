"""Architecture evaluation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent.gap_analyst import GapAnalyst
from agent.report_generator import ReportGenerator
from app.dependencies import get_bedrock, get_project_or_404, get_storage
from app.models.schemas import EvaluationReport, Project, ReportResponse

router = APIRouter(prefix="/projects", tags=["evaluation"])


@router.post("/{project_id}/evaluate", response_model=EvaluationReport)
def evaluate_architecture(project_id: str) -> EvaluationReport:
    project = get_project_or_404(project_id)
    if project.architecture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Architecture required before evaluation",
        )
    analyst = GapAnalyst(bedrock_client=get_bedrock())
    report = analyst.analyze(
        project_id=project.id,
        architecture=project.architecture,
        requirements=project.requirements,
    )
    project.evaluation = report
    get_storage().save_project(project)
    return report


@router.get("/{project_id}/report", response_model=ReportResponse)
def get_report(project_id: str) -> ReportResponse:
    project = get_project_or_404(project_id)
    return ReportGenerator().generate(project)
