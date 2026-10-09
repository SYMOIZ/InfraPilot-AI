"""Deterministic security evaluation rules."""

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


class SecurityRules:
    category = "security"

    def evaluate(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> List[EvaluationFinding]:
        findings: List[EvaluationFinding] = []
        services = _service_ids(architecture)

        # S3 encryption
        s3_nodes = _nodes_by_service(architecture, "s3")
        if not s3_nodes:
            findings.append(
                EvaluationFinding(
                    rule_id="SEC-S3-001",
                    category=self.category,
                    title="S3 encryption check",
                    status=RuleStatus.NOT_APPLICABLE,
                    message="No S3 buckets present in architecture.",
                    source="rules",
                )
            )
        else:
            for node in s3_nodes:
                encryption = node.props.get("encryption")
                public = node.props.get("public", False)
                if encryption in (None, "", False, "none"):
                    if "encryption" not in node.props:
                        findings.append(
                            EvaluationFinding(
                                rule_id="SEC-S3-001",
                                category=self.category,
                                title="S3 encryption evidence missing",
                                status=RuleStatus.UNKNOWN,
                                severity="high",
                                message=(
                                    f"S3 node '{node.label}' has no encryption "
                                    "property — cannot confirm encryption."
                                ),
                                evidence=f"node={node.id} props={node.props}",
                                recommendation=(
                                    "Enable SSE-S3 or SSE-KMS and record "
                                    "encryption=true in architecture props."
                                ),
                                source="rules",
                            )
                        )
                    else:
                        findings.append(
                            EvaluationFinding(
                                rule_id="SEC-S3-001",
                                category=self.category,
                                title="S3 without encryption",
                                status=RuleStatus.FAIL,
                                severity="critical",
                                message=(
                                    f"S3 node '{node.label}' explicitly lacks "
                                    "encryption."
                                ),
                                evidence=f"node={node.id} encryption={encryption}",
                                recommendation="Enable default encryption (SSE-S3/SSE-KMS).",
                                source="rules",
                            )
                        )
                else:
                    findings.append(
                        EvaluationFinding(
                            rule_id="SEC-S3-001",
                            category=self.category,
                            title="S3 encryption enabled",
                            status=RuleStatus.PASS,
                            message=f"S3 node '{node.label}' has encryption configured.",
                            evidence=f"encryption={encryption}",
                            source="rules",
                        )
                    )

                if public is True and encryption in (None, "", False, "none"):
                    findings.append(
                        EvaluationFinding(
                            rule_id="SEC-S3-002",
                            category=self.category,
                            title="Public S3 without encryption",
                            status=RuleStatus.FAIL,
                            severity="critical",
                            message=(
                                f"Public S3 node '{node.label}' without "
                                "encryption is a critical risk."
                            ),
                            evidence=f"public={public} encryption={encryption}",
                            recommendation=(
                                "Block public access or encrypt and restrict "
                                "via CloudFront/OAC."
                            ),
                            source="rules",
                        )
                    )
                elif public is True:
                    findings.append(
                        EvaluationFinding(
                            rule_id="SEC-S3-002",
                            category=self.category,
                            title="Public S3 bucket",
                            status=RuleStatus.WARNING,
                            severity="high",
                            message=(
                                f"S3 node '{node.label}' is marked public. "
                                "Prefer private buckets with CloudFront OAC."
                            ),
                            evidence=f"public={public}",
                            recommendation="Use CloudFront + OAC; block public access.",
                            source="rules",
                        )
                    )

        # IAM wildcards
        iam_nodes = _nodes_by_service(architecture, "iam")
        if not iam_nodes:
            findings.append(
                EvaluationFinding(
                    rule_id="SEC-IAM-001",
                    category=self.category,
                    title="IAM least privilege",
                    status=RuleStatus.UNKNOWN,
                    severity="medium",
                    message=(
                        "No IAM nodes present — cannot verify least-privilege. "
                        "Missing evidence is not treated as a Pass."
                    ),
                    recommendation="Document IAM roles/policies in the architecture.",
                    source="rules",
                )
            )
        else:
            for node in iam_nodes:
                wildcard = node.props.get("wildcard_actions") or node.props.get(
                    "has_wildcard"
                )
                if wildcard is True or wildcard == "*":
                    findings.append(
                        EvaluationFinding(
                            rule_id="SEC-IAM-001",
                            category=self.category,
                            title="IAM wildcard actions",
                            status=RuleStatus.FAIL,
                            severity="critical",
                            message=(
                                f"IAM node '{node.label}' uses wildcard actions."
                            ),
                            evidence=f"props={node.props}",
                            recommendation="Scope IAM actions to least privilege.",
                            source="rules",
                        )
                    )
                elif wildcard is False:
                    findings.append(
                        EvaluationFinding(
                            rule_id="SEC-IAM-001",
                            category=self.category,
                            title="IAM least privilege indicated",
                            status=RuleStatus.PASS,
                            message=f"IAM node '{node.label}' indicates no wildcards.",
                            evidence=f"props={node.props}",
                            source="rules",
                        )
                    )
                else:
                    findings.append(
                        EvaluationFinding(
                            rule_id="SEC-IAM-001",
                            category=self.category,
                            title="IAM policy evidence missing",
                            status=RuleStatus.UNKNOWN,
                            severity="medium",
                            message=(
                                f"IAM node '{node.label}' lacks wildcard/policy "
                                "evidence — not scored as Pass."
                            ),
                            evidence=f"props={node.props}",
                            source="rules",
                        )
                    )

        # WAF for public web
        if requirements and requirements.workload.value in ("web", "api"):
            if "waf" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="SEC-WAF-001",
                        category=self.category,
                        title="WAF present for public workload",
                        status=RuleStatus.PASS,
                        message="AWS WAF is included for web/API workload.",
                        source="rules",
                    )
                )
            elif "cloudfront" in services or "api_gateway" in services or "alb" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="SEC-WAF-001",
                        category=self.category,
                        title="WAF missing for public edge",
                        status=RuleStatus.WARNING,
                        severity="medium",
                        message=(
                            "Public web/API edge present without WAF."
                        ),
                        recommendation="Add AWS WAF on CloudFront, ALB, or API Gateway.",
                        source="rules",
                    )
                )

        # Encryption for sensitive data
        if requirements and requirements.data_sensitivity.value in (
            "confidential",
            "regulated",
        ):
            if "kms" in services:
                findings.append(
                    EvaluationFinding(
                        rule_id="SEC-KMS-001",
                        category=self.category,
                        title="KMS for sensitive data",
                        status=RuleStatus.PASS,
                        message="KMS present for confidential/regulated data.",
                        source="rules",
                    )
                )
            else:
                findings.append(
                    EvaluationFinding(
                        rule_id="SEC-KMS-001",
                        category=self.category,
                        title="KMS missing for sensitive data",
                        status=RuleStatus.FAIL,
                        severity="high",
                        message=(
                            "Confidential/regulated data requires KMS evidence."
                        ),
                        recommendation="Add AWS KMS and encrypt data at rest.",
                        source="rules",
                    )
                )

        return findings
