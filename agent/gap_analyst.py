"""Combine deterministic rules with optional AI gap analysis."""

from __future__ import annotations

from typing import Any, List, Optional
from uuid import uuid4

from app.models.schemas import (
    Architecture,
    EvaluationFinding,
    EvaluationReport,
    Requirements,
    RuleStatus,
    ScoreReport,
)
from rules.engine import RulesEngine, score_findings


class GapAnalyst:
    """Runs rules engine and supplements with AI gap narrative (mock-safe)."""

    def __init__(self, bedrock_client: Any = None) -> None:
        self.engine = RulesEngine()
        self.bedrock = bedrock_client

    def analyze(
        self,
        project_id: str,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> EvaluationReport:
        findings = self.engine.evaluate(architecture, requirements)
        findings.extend(self._ai_gaps(architecture, requirements))
        scores = score_findings(findings)
        gaps = [
            f.title
            for f in findings
            if f.status in (RuleStatus.FAIL, RuleStatus.WARNING, RuleStatus.UNKNOWN)
        ]
        summary = self._summarize(findings, scores)
        return EvaluationReport(
            project_id=project_id,
            findings=findings,
            scores=scores,
            summary=summary,
            gaps=gaps,
        )

    def _ai_gaps(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements],
    ) -> List[EvaluationFinding]:
        if self.bedrock is not None:
            try:
                extra = self.bedrock.analyze_gaps(
                    architecture.model_dump(by_alias=True),
                    requirements.model_dump() if requirements else {},
                )
                if isinstance(extra, list):
                    out: List[EvaluationFinding] = []
                    for item in extra:
                        if isinstance(item, EvaluationFinding):
                            out.append(item)
                        elif isinstance(item, dict):
                            item.setdefault("source", "ai")
                            item.setdefault("id", str(uuid4()))
                            out.append(EvaluationFinding.model_validate(item))
                    return out
            except Exception:
                pass

        # Deterministic AI-style gaps without inventing Pass for missing evidence
        services = {n.service_id for n in architecture.nodes}
        findings: List[EvaluationFinding] = []
        if requirements and requirements.workload.value == "web":
            if "cloudfront" not in services and "alb" not in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="AI-GAP-001",
                        category="best_practices",
                        title="No global/edge entry point",
                        status=RuleStatus.WARNING,
                        severity="medium",
                        message=(
                            "Web workload without CloudFront or ALB may lack "
                            "a clear edge entry pattern."
                        ),
                        recommendation="Add CloudFront or ALB as the public entry.",
                        source="ai",
                    )
                )
        if "cloudwatch" not in services:
            findings.append(
                EvaluationFinding(
                    rule_id="AI-GAP-002",
                    category="reliability",
                    title="Observability gap",
                    status=RuleStatus.UNKNOWN,
                    severity="medium",
                    message=(
                        "No CloudWatch evidence in diagram — observability "
                        "cannot be confirmed as Pass."
                    ),
                    recommendation="Document metrics, logs, and alarms.",
                    source="ai",
                )
            )
        return findings

    def _summarize(
        self,
        findings: List[EvaluationFinding],
        scores: ScoreReport,
    ) -> str:
        fails = sum(1 for f in findings if f.status == RuleStatus.FAIL)
        warns = sum(1 for f in findings if f.status == RuleStatus.WARNING)
        unknowns = sum(1 for f in findings if f.status == RuleStatus.UNKNOWN)
        return (
            f"Overall score {scores.overall}/100 with {fails} fail(s), "
            f"{warns} warning(s), and {unknowns} unknown (insufficient evidence). "
            "Unknown is never treated as Pass."
        )
