"""Deterministic reliability / availability rules."""

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


def _nodes_by_service(architecture: Architecture, service_id: str):
    return [n for n in architecture.nodes if n.service_id == service_id]


class ReliabilityRules:
    category = "reliability"

    def evaluate(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> List[EvaluationFinding]:
        findings: List[EvaluationFinding] = []
        services = _service_ids(architecture)
        availability = (
            requirements.availability.value if requirements else "standard"
        )

        # Multi-AZ for HA
        multi_az_services = ("rds", "ecs", "eks", "alb", "ec2")
        for svc in multi_az_services:
            nodes = _nodes_by_service(architecture, svc)
            if not nodes:
                continue
            for node in nodes:
                multi_az = node.props.get("multi_az")
                if availability in ("high", "critical"):
                    if multi_az is True:
                        findings.append(
                            EvaluationFinding(
                                rule_id="REL-AZ-001",
                                category=self.category,
                                title=f"Multi-AZ for {svc}",
                                status=RuleStatus.PASS,
                                message=(
                                    f"{node.label} indicates multi-AZ for "
                                    f"{availability} availability."
                                ),
                                evidence=f"multi_az={multi_az}",
                                source="rules",
                            )
                        )
                    elif multi_az is False:
                        status = (
                            RuleStatus.FAIL
                            if availability == "critical"
                            else RuleStatus.WARNING
                        )
                        findings.append(
                            EvaluationFinding(
                                rule_id="REL-AZ-001",
                                category=self.category,
                                title=f"Missing multi-AZ for {svc}",
                                status=status,
                                severity="high",
                                message=(
                                    f"{node.label} is not multi-AZ but "
                                    f"availability target is {availability}."
                                ),
                                evidence=f"multi_az={multi_az}",
                                recommendation="Enable multi-AZ / multi-AZ deployment.",
                                source="rules",
                            )
                        )
                    else:
                        findings.append(
                            EvaluationFinding(
                                rule_id="REL-AZ-001",
                                category=self.category,
                                title=f"Multi-AZ evidence missing for {svc}",
                                status=RuleStatus.UNKNOWN,
                                severity="medium",
                                message=(
                                    f"No multi_az property on '{node.label}'. "
                                    "Cannot confirm HA posture."
                                ),
                                evidence=f"props={node.props}",
                                source="rules",
                            )
                        )

        if availability in ("high", "critical") and not any(
            _nodes_by_service(architecture, s) for s in multi_az_services
        ):
            # Serverless often multi-AZ by default
            if services & {"lambda", "dynamodb", "s3", "api_gateway"}:
                findings.append(
                    EvaluationFinding(
                        rule_id="REL-AZ-002",
                        category=self.category,
                        title="Managed multi-AZ serverless",
                        status=RuleStatus.PASS,
                        message=(
                            "Serverless managed services typically provide "
                            "regional multi-AZ resilience by default."
                        ),
                        evidence=f"services={sorted(services)}",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="REL-AZ-002",
                        category=self.category,
                        title="HA posture unclear",
                        status=RuleStatus.WARNING,
                        message=(
                            "High/critical availability requested but no "
                            "clear multi-AZ or managed regional services found."
                        ),
                        source="rules",
                    )
                )

        # CloudWatch monitoring
        if "cloudwatch" in services:
            findings.append(
                EvaluationFinding(
                    rule_id="REL-MON-001",
                    category=self.category,
                    title="CloudWatch monitoring present",
                    status=RuleStatus.PASS,
                    message="CloudWatch included for observability.",
                    source="rules",
                )
            )
        else:
            findings.append(
                EvaluationFinding(
                    rule_id="REL-MON-001",
                    category=self.category,
                    title="CloudWatch missing",
                    status=RuleStatus.WARNING,
                    severity="medium",
                    message="No CloudWatch node — monitoring posture unknown/weak.",
                    recommendation="Add CloudWatch metrics, alarms, and logs.",
                    source="rules",
                )
            )

        # Backup / recovery
        if requirements and requirements.recovery not in (
            "best-effort",
            "none",
            "",
        ):
            stateful = _nodes_by_service(architecture, "rds") + _nodes_by_service(
                architecture, "dynamodb"
            )
            if not stateful:
                findings.append(
                    EvaluationFinding(
                        rule_id="REL-DR-001",
                        category=self.category,
                        title="Recovery target without stateful store",
                        status=RuleStatus.NOT_APPLICABLE,
                        message="No RDS/DynamoDB nodes for backup checks.",
                        source="rules",
                    )
                )
            else:
                for node in stateful:
                    backup = node.props.get("backup") or node.props.get("pit_recovery")
                    if backup:
                        findings.append(
                            EvaluationFinding(
                                rule_id="REL-DR-001",
                                category=self.category,
                                title="Backup/recovery indicated",
                                status=RuleStatus.PASS,
                                message=f"{node.label} indicates backup/recovery.",
                                evidence=f"backup={backup}",
                                source="rules",
                            )
                        )
                    else:
                        findings.append(
                            EvaluationFinding(
                                rule_id="REL-DR-001",
                                category=self.category,
                                title="Backup evidence missing",
                                status=RuleStatus.WARNING,
                                severity="medium",
                                message=(
                                    f"Recovery expectation '{requirements.recovery}' "
                                    f"but '{node.label}' has no backup props."
                                ),
                                recommendation="Enable backups / PITR as appropriate.",
                                source="rules",
                            )
                        )

        return findings
