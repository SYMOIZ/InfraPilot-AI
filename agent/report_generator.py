"""Generate executive evaluation / optimization reports."""

from __future__ import annotations

from typing import Optional

from app.models.schemas import (
    Architecture,
    EvaluationReport,
    OptimizationProposal,
    Project,
    ReportResponse,
    Requirements,
)


class ReportGenerator:
    """Assembles a structured report from project state."""

    def generate(self, project: Project) -> ReportResponse:
        requirements = project.requirements
        architecture = project.architecture
        evaluation = project.evaluation
        optimization = project.optimization

        exec_summary = self._executive_summary(
            project.name,
            requirements,
            architecture,
            evaluation,
            optimization,
        )
        return ReportResponse(
            project_id=project.id,
            title=f"InfraPilot Report — {project.name}",
            executive_summary=exec_summary,
            requirements=requirements,
            architecture=architecture,
            evaluation=evaluation,
            optimization=optimization,
        )

    def _executive_summary(
        self,
        name: str,
        requirements: Optional[Requirements],
        architecture: Optional[Architecture],
        evaluation: Optional[EvaluationReport],
        optimization: Optional[OptimizationProposal],
    ) -> str:
        parts = [f"Project '{name}' architecture design and evaluation report."]
        if requirements:
            parts.append(
                f"Purpose: {requirements.purpose}. Workload: {requirements.workload.value}. "
                f"Region: {requirements.region}. Availability: {requirements.availability.value}."
            )
        if architecture:
            services = sorted({n.service_id for n in architecture.nodes})
            parts.append(
                f"Architecture '{architecture.name}' includes {len(architecture.nodes)} "
                f"services ({', '.join(services)})."
            )
        if evaluation:
            parts.append(
                f"Evaluation overall score: {evaluation.scores.overall}/100. "
                f"{evaluation.summary}"
            )
        if optimization:
            parts.append(
                f"Optimization proposes {len(optimization.changes)} change(s). "
                f"{optimization.cost_notes}"
            )
        parts.append(
            "InfraPilot does not deploy infrastructure or generate "
            "Terraform/CloudFormation."
        )
        return " ".join(parts)
