"""Propose optimized architectures respecting requirements and budget."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, List, Optional
from uuid import uuid4

from app.models.schemas import (
    Architecture,
    ArchitectureEdge,
    ArchitectureNode,
    OptimizationChange,
    OptimizationProposal,
    Requirements,
)


class OptimizationPlanner:
    """Produces an improved architecture and a clear diff."""

    def __init__(self, bedrock_client: Any = None) -> None:
        self.bedrock = bedrock_client

    def optimize(
        self,
        project_id: str,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> OptimizationProposal:
        if self.bedrock is not None:
            try:
                result = self.bedrock.optimize_architecture(
                    architecture.model_dump(by_alias=True),
                    requirements.model_dump() if requirements else {},
                )
                if isinstance(result, OptimizationProposal):
                    return result
            except Exception:
                pass

        optimized = deepcopy(architecture)
        optimized.id = str(uuid4())
        optimized.source = "optimized"
        optimized.name = f"Optimized: {architecture.name}"
        changes: List[OptimizationChange] = []
        services = {n.service_id for n in optimized.nodes}

        def has(service_id: str) -> bool:
            return service_id in services

        def add_node(node: ArchitectureNode, rationale: str, cats: List[str]) -> None:
            optimized.nodes.append(node)
            services.add(node.service_id)
            changes.append(
                OptimizationChange(
                    change_type="add",
                    service_id=node.service_id,
                    description=f"Add {node.label}",
                    rationale=rationale,
                    impact_categories=cats,
                )
            )

        # CloudWatch
        if not has("cloudwatch"):
            add_node(
                ArchitectureNode(
                    id=f"opt-cw-{uuid4().hex[:6]}",
                    service_id="cloudwatch",
                    label="CloudWatch",
                    props={"alarms": True},
                    x=620,
                    y=320,
                ),
                "Add observability for reliability and operations.",
                ["reliability", "best_practices"],
            )

        # WAF for web/api
        if requirements and requirements.workload.value in ("web", "api"):
            if not has("waf") and (has("cloudfront") or has("api_gateway") or has("alb")):
                add_node(
                    ArchitectureNode(
                        id=f"opt-waf-{uuid4().hex[:6]}",
                        service_id="waf",
                        label="AWS WAF",
                        props={},
                        x=40,
                        y=40,
                    ),
                    "Protect public edge with WAF.",
                    ["security"],
                )
                edge_target = next(
                    (
                        n.id
                        for n in optimized.nodes
                        if n.service_id in ("cloudfront", "api_gateway", "alb")
                    ),
                    None,
                )
                if edge_target:
                    waf_id = optimized.nodes[-1].id
                    optimized.edges.append(
                        ArchitectureEdge(
                            id=f"opt-e-{uuid4().hex[:6]}",
                            **{"from": waf_id, "to": edge_target, "label": "protect"},
                        )
                    )

        # KMS for sensitive data
        if requirements and requirements.data_sensitivity.value in (
            "confidential",
            "regulated",
        ):
            if not has("kms"):
                add_node(
                    ArchitectureNode(
                        id=f"opt-kms-{uuid4().hex[:6]}",
                        service_id="kms",
                        label="KMS Keys",
                        props={},
                        x=620,
                        y=40,
                    ),
                    "Encrypt sensitive data with customer-managed keys where appropriate.",
                    ["security"],
                )

        # Fix public S3 / missing encryption
        for node in optimized.nodes:
            if node.service_id == "s3":
                if node.props.get("public") is True:
                    node.props["public"] = False
                    changes.append(
                        OptimizationChange(
                            change_type="modify",
                            service_id="s3",
                            description=f"Set {node.label} to private",
                            rationale="Prefer private buckets with CloudFront OAC.",
                            impact_categories=["security"],
                        )
                    )
                if node.props.get("encryption") in (None, "", False, "none"):
                    node.props["encryption"] = "AES256"
                    changes.append(
                        OptimizationChange(
                            change_type="modify",
                            service_id="s3",
                            description=f"Enable encryption on {node.label}",
                            rationale="Encrypt data at rest.",
                            impact_categories=["security"],
                        )
                    )

        # IAM wildcards
        for node in optimized.nodes:
            if node.service_id == "iam" and (
                node.props.get("wildcard_actions") is True
                or node.props.get("has_wildcard") is True
            ):
                node.props["wildcard_actions"] = False
                node.props["has_wildcard"] = False
                changes.append(
                    OptimizationChange(
                        change_type="modify",
                        service_id="iam",
                        description=f"Remove wildcards on {node.label}",
                        rationale="Enforce least privilege.",
                        impact_categories=["security"],
                    )
                )

        # Multi-AZ for HA
        if requirements and requirements.availability.value in ("high", "critical"):
            for node in optimized.nodes:
                if node.service_id in ("rds", "ecs", "eks", "alb", "ec2", "vpc"):
                    if node.props.get("multi_az") is not True:
                        node.props["multi_az"] = True
                        changes.append(
                            OptimizationChange(
                                change_type="modify",
                                service_id=node.service_id,
                                description=f"Enable multi-AZ on {node.label}",
                                rationale=f"Meet {requirements.availability.value} availability.",
                                impact_categories=["reliability"],
                            )
                        )

        # Budget: prefer DynamoDB over RDS if low budget and both present conceptually
        if requirements and requirements.budget.lower() in ("low", "minimal", "constrained"):
            if has("rds") and not has("dynamodb"):
                # Suggest replace rather than silently deleting without note
                rds_nodes = [n for n in optimized.nodes if n.service_id == "rds"]
                for rn in rds_nodes:
                    optimized.nodes = [n for n in optimized.nodes if n.id != rn.id]
                    optimized.edges = [
                        e
                        for e in optimized.edges
                        if e.from_node != rn.id and e.to_node != rn.id
                    ]
                    changes.append(
                        OptimizationChange(
                            change_type="remove",
                            service_id="rds",
                            description=f"Remove {rn.label}",
                            rationale="Low budget — prefer serverless datastore.",
                            impact_categories=["cost"],
                        )
                    )
                add_node(
                    ArchitectureNode(
                        id=f"opt-ddb-{uuid4().hex[:6]}",
                        service_id="dynamodb",
                        label="DynamoDB (cost-optimized)",
                        props={"capacity_mode": "on-demand", "encryption": True},
                        x=480,
                        y=220,
                    ),
                    "Replace RDS with DynamoDB for lower baseline cost (qualitative).",
                    ["cost", "scalability"],
                )

        # CloudFront for web + S3
        if requirements and requirements.workload.value == "web":
            if has("s3") and not has("cloudfront"):
                add_node(
                    ArchitectureNode(
                        id=f"opt-cf-{uuid4().hex[:6]}",
                        service_id="cloudfront",
                        label="CloudFront",
                        props={},
                        x=80,
                        y=40,
                    ),
                    "CDN reduces origin load and improves global latency.",
                    ["cost", "scalability", "best_practices"],
                )

        if not changes:
            changes.append(
                OptimizationChange(
                    change_type="modify",
                    service_id=None,
                    description="No structural changes required",
                    rationale="Architecture already aligns with stated requirements.",
                    impact_categories=["best_practices"],
                )
            )

        summary = (
            f"Proposed {len(changes)} optimization change(s) respecting "
            f"requirements and qualitative budget guidance."
        )
        return OptimizationProposal(
            project_id=project_id,
            original=architecture,
            optimized=optimized,
            changes=changes,
            summary=summary,
            cost_notes=(
                "Qualitative cost guidance only — InfraPilot does not invent "
                "AWS list prices or generate Terraform/CloudFormation."
            ),
        )

    @staticmethod
    def diff(
        original: Architecture,
        optimized: Architecture,
    ) -> List[OptimizationChange]:
        """Compute a simple service-set diff."""
        orig = {n.service_id for n in original.nodes}
        opt = {n.service_id for n in optimized.nodes}
        changes: List[OptimizationChange] = []
        for sid in sorted(opt - orig):
            changes.append(
                OptimizationChange(
                    change_type="add",
                    service_id=sid,
                    description=f"Added service {sid}",
                    rationale="Present in optimized architecture",
                    impact_categories=[],
                )
            )
        for sid in sorted(orig - opt):
            changes.append(
                OptimizationChange(
                    change_type="remove",
                    service_id=sid,
                    description=f"Removed service {sid}",
                    rationale="Removed in optimized architecture",
                    impact_categories=[],
                )
            )
        return changes
