"""Deterministic AWS well-architected / best-practice rules."""

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


class BestPracticeRules:
    category = "best_practices"

    def evaluate(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> List[EvaluationFinding]:
        findings: List[EvaluationFinding] = []
        services = _service_ids(architecture)

        # VPC for non-serverless-only workloads with EC2/RDS/ECS/EKS
        needs_vpc = bool(services & {"ec2", "rds", "ecs", "eks", "alb"})
        if needs_vpc:
            if "vpc" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-VPC-001",
                        category=self.category,
                        title="VPC boundary present",
                        status=RuleStatus.PASS,
                        message="VPC included for network-isolated compute/data.",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-VPC-001",
                        category=self.category,
                        title="VPC missing",
                        status=RuleStatus.WARNING,
                        severity="medium",
                        message=(
                            "Compute/database services typically belong in a VPC."
                        ),
                        recommendation="Add VPC with public/private subnet design.",
                        source="rules",
                    )
                )
        else:
            findings.append(
                EvaluationFinding(
                    rule_id="BP-VPC-001",
                    category=self.category,
                    title="VPC check",
                    status=RuleStatus.NOT_APPLICABLE,
                    message="No VPC-bound services detected.",
                    source="rules",
                )
            )

        # Secrets Manager for apps with databases
        if services & {"rds", "dynamodb"} and "lambda" in services:
            if "secrets_manager" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-SEC-001",
                        category=self.category,
                        title="Secrets Manager present",
                        status=RuleStatus.PASS,
                        message="Secrets Manager included for credential hygiene.",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-SEC-001",
                        category=self.category,
                        title="Secrets Manager missing",
                        status=RuleStatus.WARNING,
                        severity="low",
                        message=(
                            "App + data store without Secrets Manager — "
                            "prefer managed secrets over env hardcoding."
                        ),
                        recommendation="Add Secrets Manager (or SSM Parameter Store).",
                        source="rules",
                    )
                )

        # Cognito / auth for public APIs
        if "api_gateway" in services or "alb" in services:
            if "cognito" in services or "iam" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-AUTH-001",
                        category=self.category,
                        title="Auth component present",
                        status=RuleStatus.PASS,
                        message="Auth-related service (Cognito/IAM) present at edge.",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-AUTH-001",
                        category=self.category,
                        title="Auth component unclear",
                        status=RuleStatus.WARNING,
                        severity="medium",
                        message=(
                            "Public API/ALB without Cognito/IAM node — "
                            "auth posture is unclear."
                        ),
                        recommendation="Document Cognito, IAM, or external IdP.",
                        source="rules",
                    )
                )

        # Region alignment
        if requirements and requirements.region:
            arch_region = architecture.metadata.get("region")
            if arch_region and arch_region != requirements.region:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-REG-001",
                        category=self.category,
                        title="Region mismatch",
                        status=RuleStatus.WARNING,
                        message=(
                            f"Architecture region '{arch_region}' differs from "
                            f"requirements '{requirements.region}'."
                        ),
                        source="rules",
                    )
                )
            elif arch_region:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-REG-001",
                        category=self.category,
                        title="Region aligned",
                        status=RuleStatus.PASS,
                        message=f"Architecture region matches '{requirements.region}'.",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="BP-REG-001",
                        category=self.category,
                        title="Architecture region not set",
                        status=RuleStatus.UNKNOWN,
                        message="Architecture metadata.region not specified.",
                        source="rules",
                    )
                )

        # Diagram has edges (data flow documented)
        if architecture.nodes and not architecture.edges:
            findings.append(
                EvaluationFinding(
                    rule_id="BP-FLOW-001",
                    category=self.category,
                    title="Missing data-flow edges",
                    status=RuleStatus.WARNING,
                    severity="low",
                    message="Architecture has nodes but no edges documenting data flow.",
                    recommendation="Add edges between communicating services.",
                    source="rules",
                )
            )
        elif architecture.edges:
            findings.append(
                EvaluationFinding(
                    rule_id="BP-FLOW-001",
                    category=self.category,
                    title="Data-flow edges present",
                    status=RuleStatus.PASS,
                    message="Architecture documents connections between services.",
                    source="rules",
                )
            )

        return findings
