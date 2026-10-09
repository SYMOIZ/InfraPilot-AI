"""Deterministic cost-related evaluation rules (qualitative only)."""

from __future__ import annotations

from typing import List, Optional, Set

from app.models.schemas import (
    Architecture,
    EvaluationFinding,
    Requirements,
    RuleStatus,
)


def _service_ids(architecture: Architecture) -> Set[str]:
    return {n.service_id for n in architecture.nodes}


class CostRules:
    category = "cost"

    def evaluate(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> List[EvaluationFinding]:
        findings: List[EvaluationFinding] = []
        services = _service_ids(architecture)
        budget = (requirements.budget if requirements else "moderate").lower()

        # Prefer serverless for low budget web/api
        expensive = {"eks", "ecs", "rds"}
        serverless = {"lambda", "dynamodb", "s3", "api_gateway", "sqs", "sns"}
        has_expensive = bool(services & expensive)
        has_serverless = bool(services & serverless)

        if budget in ("low", "minimal", "constrained"):
            if has_expensive and not has_serverless:
                findings.append(
                    EvaluationFinding(
                        rule_id="COST-001",
                        category=self.category,
                        title="Low budget vs managed compute/DB",
                        status=RuleStatus.WARNING,
                        severity="medium",
                        message=(
                            "Low budget indicated but architecture uses "
                            "typically higher fixed-cost services "
                            "(EKS/ECS/RDS) without serverless alternatives."
                        ),
                        evidence=f"services={sorted(services)} budget={budget}",
                        recommendation=(
                            "Consider Lambda + DynamoDB/S3 for lower baseline "
                            "cost. Qualitative guidance only — no prices invented."
                        ),
                        source="rules",
                    )
                )
            elif has_serverless:
                findings.append(
                    EvaluationFinding(
                        rule_id="COST-001",
                        category=self.category,
                        title="Serverless-friendly for budget",
                        status=RuleStatus.PASS,
                        message=(
                            "Architecture includes serverless components "
                            "aligned with a constrained budget."
                        ),
                        evidence=f"serverless={sorted(services & serverless)}",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="COST-001",
                        category=self.category,
                        title="Budget alignment unclear",
                        status=RuleStatus.UNKNOWN,
                        message="Insufficient evidence to judge cost alignment.",
                        source="rules",
                    )
                )
        else:
            findings.append(
                EvaluationFinding(
                    rule_id="COST-001",
                    category=self.category,
                    title="Budget flexibility",
                    status=RuleStatus.PASS,
                    message=(
                        f"Budget '{budget}' allows broader service choices. "
                        "No AWS list prices are asserted."
                    ),
                    source="rules",
                )
            )

        # NAT / multi-AZ cost awareness — qualitative
        if "vpc" in services and requirements and requirements.availability.value == "critical":
            findings.append(
                EvaluationFinding(
                    rule_id="COST-002",
                    category=self.category,
                    title="HA networking cost awareness",
                    status=RuleStatus.WARNING,
                    severity="low",
                    message=(
                        "Critical availability with VPC typically implies "
                        "multi-AZ NAT/egress costs — plan qualitatively."
                    ),
                    recommendation=(
                        "Review NAT Gateway and cross-AZ traffic implications; "
                        "do not rely on invented price figures."
                    ),
                    source="rules",
                )
            )
        elif "vpc" not in services:
            findings.append(
                EvaluationFinding(
                    rule_id="COST-002",
                    category=self.category,
                    title="VPC cost check",
                    status=RuleStatus.NOT_APPLICABLE,
                    message="No VPC node — NAT/egress cost rule not applicable.",
                    source="rules",
                )
            )

        # CloudFront for static delivery
        if "s3" in services and "cloudfront" not in services:
            if requirements and requirements.workload.value == "web":
                findings.append(
                    EvaluationFinding(
                        rule_id="COST-003",
                        category=self.category,
                        title="CDN for static content",
                        status=RuleStatus.WARNING,
                        severity="low",
                        message=(
                            "Web workload with S3 but no CloudFront may "
                            "increase origin egress relative to CDN caching."
                        ),
                        recommendation="Add CloudFront for static assets (qualitative).",
                        source="rules",
                    )
                )

        return findings
