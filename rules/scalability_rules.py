"""Deterministic scalability evaluation rules."""

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


class ScalabilityRules:
    category = "scalability"

    def evaluate(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> List[EvaluationFinding]:
        findings: List[EvaluationFinding] = []
        services = _service_ids(architecture)
        scale = (requirements.scalability if requirements else "moderate").lower()
        traffic = (requirements.traffic if requirements else "low").lower()

        autoscaling = {"lambda", "ecs", "eks", "dynamodb", "api_gateway", "alb", "sqs"}
        fixed = {"ec2"}

        if scale in ("high", "elastic", "auto") or traffic in (
            "high",
            "burst",
            "spiky",
        ):
            if services & autoscaling:
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-001",
                        category=self.category,
                        title="Elastic services present",
                        status=RuleStatus.PASS,
                        message=(
                            "Architecture includes services that scale "
                            "elastically for high/spiky demand."
                        ),
                        evidence=f"elastic={sorted(services & autoscaling)}",
                        source="rules",
                    )
                )
            elif services & fixed and not (services & autoscaling):
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-001",
                        category=self.category,
                        title="Fixed capacity for high scale",
                        status=RuleStatus.FAIL,
                        severity="high",
                        message=(
                            "High scalability/traffic indicated but only "
                            "fixed EC2-style capacity found."
                        ),
                        recommendation=(
                            "Add ALB + Auto Scaling, Lambda, or container "
                            "orchestration with autoscaling."
                        ),
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-001",
                        category=self.category,
                        title="Scalability evidence incomplete",
                        status=RuleStatus.UNKNOWN,
                        message="Cannot confirm elastic scaling posture.",
                        source="rules",
                    )
                )
        else:
            findings.append(
                EvaluationFinding(
                    rule_id="SCALE-001",
                    category=self.category,
                    title="Moderate scale needs",
                    status=RuleStatus.PASS,
                    message="Scale requirements appear moderate; current design acceptable.",
                    source="rules",
                )
            )

        # Decoupling with queues
        if traffic in ("high", "burst", "spiky") and "sqs" not in services and "sns" not in services:
            if "lambda" in services or "ecs" in services or "ec2" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-002",
                        category=self.category,
                        title="Async decoupling recommended",
                        status=RuleStatus.WARNING,
                        severity="low",
                        message=(
                            "High/bursty traffic without SQS/SNS may couple "
                            "producers and consumers tightly."
                        ),
                        recommendation="Consider SQS/SNS for buffering and fan-out.",
                        source="rules",
                    )
                )
        else:
            if "sqs" in services or "sns" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-002",
                        category=self.category,
                        title="Messaging for decoupling",
                        status=RuleStatus.PASS,
                        message="SQS/SNS present for asynchronous decoupling.",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-002",
                        category=self.category,
                        title="Messaging check",
                        status=RuleStatus.NOT_APPLICABLE,
                        message="Async messaging not required for stated traffic.",
                        source="rules",
                    )
                )

        # DynamoDB on-demand / capacity mode evidence
        ddb = [n for n in architecture.nodes if n.service_id == "dynamodb"]
        for node in ddb:
            mode = node.props.get("capacity_mode")
            if mode:
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-003",
                        category=self.category,
                        title="DynamoDB capacity mode set",
                        status=RuleStatus.PASS,
                        message=f"{node.label} capacity_mode={mode}.",
                        evidence=f"capacity_mode={mode}",
                        source="rules",
                    )
                )
            elif scale in ("high", "elastic", "auto"):
                findings.append(
                    EvaluationFinding(
                        rule_id="SCALE-003",
                        category=self.category,
                        title="DynamoDB capacity mode unknown",
                        status=RuleStatus.UNKNOWN,
                        message=(
                            f"{node.label} missing capacity_mode — prefer "
                            "on-demand for unpredictable traffic."
                        ),
                        source="rules",
                    )
                )

        return findings
