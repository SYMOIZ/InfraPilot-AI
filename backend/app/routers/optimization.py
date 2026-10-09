"""Optimization and compare endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agent.gap_analyst import GapAnalyst
from agent.optimization_planner import OptimizationPlanner
from app.dependencies import get_bedrock, get_project_or_404, get_storage
from app.models.schemas import CompareResponse, OptimizationProposal

router = APIRouter(prefix="/projects", tags=["optimization"])


@router.post("/{project_id}/optimize", response_model=OptimizationProposal)
def optimize_architecture(project_id: str) -> OptimizationProposal:
    project = get_project_or_404(project_id)
    if project.architecture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Architecture required before optimization",
        )
    planner = OptimizationPlanner(bedrock_client=get_bedrock())
    proposal = planner.optimize(
        project_id=project.id,
        architecture=project.architecture,
        requirements=project.requirements,
    )
    project.optimization = proposal
    project.optimized_architecture = proposal.optimized
    get_storage().save_project(project)
    return proposal


@router.get("/{project_id}/compare", response_model=CompareResponse)
def compare_architectures(project_id: str) -> CompareResponse:
    project = get_project_or_404(project_id)
    if project.architecture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Original architecture required",
        )
    if project.optimized_architecture is None and project.optimization is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run optimize before compare",
        )

    optimized = project.optimized_architecture
    changes = []
    if project.optimization:
        optimized = project.optimization.optimized
        changes = project.optimization.changes

    analyst = GapAnalyst()
    original_scores = None
    optimized_scores = None
    if project.evaluation:
        original_scores = project.evaluation.scores
    else:
        _, original_scores = analyst.engine.evaluate_and_score(
            project.architecture, project.requirements
        )
    if optimized:
        _, optimized_scores = analyst.engine.evaluate_and_score(
            optimized, project.requirements
        )

    return CompareResponse(
        project_id=project_id,
        original=project.architecture,
        optimized=optimized,
        changes=changes,
        original_scores=original_scores,
        optimized_scores=optimized_scores,
    )
