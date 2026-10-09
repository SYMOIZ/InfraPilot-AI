"""Generate AWS architectures from requirements (Bedrock or deterministic mock)."""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from app.models.schemas import (
    Architecture,
    ArchitectureEdge,
    ArchitectureNode,
    Requirements,
)


def build_sample_web_architecture(
    name: str = "Sample Web App Architecture",
    region: str = "us-east-1",
) -> Architecture:
    """Deterministic demo architecture: CloudFront + API GW + Lambda + DDB + S3 + VPC."""
    nodes = [
        ArchitectureNode(
            id="n-cloudfront",
            service_id="cloudfront",
            label="CloudFront CDN",
            props={"caching": True},
            x=100,
            y=80,
        ),
        ArchitectureNode(
            id="n-s3",
            service_id="s3",
            label="Static Assets Bucket",
            props={"encryption": "AES256", "public": False},
            x=100,
            y=220,
        ),
        ArchitectureNode(
            id="n-apigw",
            service_id="api_gateway",
            label="API Gateway",
            props={"auth": "cognito"},
            x=320,
            y=80,
        ),
        ArchitectureNode(
            id="n-lambda",
            service_id="lambda",
            label="API Lambda",
            props={"runtime": "python3.12"},
            x=320,
            y=220,
        ),
        ArchitectureNode(
            id="n-ddb",
            service_id="dynamodb",
            label="App Table",
            props={"capacity_mode": "on-demand", "encryption": True, "pit_recovery": True},
            x=540,
            y=220,
        ),
        ArchitectureNode(
            id="n-vpc",
            service_id="vpc",
            label="Application VPC",
            props={"multi_az": True},
            x=320,
            y=360,
        ),
        ArchitectureNode(
            id="n-iam",
            service_id="iam",
            label="Least-Privilege Roles",
            props={"wildcard_actions": False},
            x=540,
            y=80,
        ),
        ArchitectureNode(
            id="n-cw",
            service_id="cloudwatch",
            label="CloudWatch",
            props={"alarms": True},
            x=540,
            y=360,
        ),
        ArchitectureNode(
            id="n-cognito",
            service_id="cognito",
            label="User Pool",
            props={},
            x=100,
            y=360,
        ),
        ArchitectureNode(
            id="n-waf",
            service_id="waf",
            label="AWS WAF",
            props={},
            x=100,
            y=0,
        ),
    ]
    edges = [
        ArchitectureEdge(id="e1", **{"from": "n-waf", "to": "n-cloudfront", "label": "protect"}),
        ArchitectureEdge(id="e2", **{"from": "n-cloudfront", "to": "n-s3", "label": "OAC"}),
        ArchitectureEdge(id="e3", **{"from": "n-cloudfront", "to": "n-apigw", "label": "API"}),
        ArchitectureEdge(id="e4", **{"from": "n-apigw", "to": "n-lambda", "label": "invoke"}),
        ArchitectureEdge(id="e5", **{"from": "n-lambda", "to": "n-ddb", "label": "CRUD"}),
        ArchitectureEdge(id="e6", **{"from": "n-lambda", "to": "n-vpc", "label": "ENI"}),
        ArchitectureEdge(id="e7", **{"from": "n-iam", "to": "n-lambda", "label": "role"}),
        ArchitectureEdge(id="e8", **{"from": "n-cognito", "to": "n-apigw", "label": "authorizer"}),
        ArchitectureEdge(id="e9", **{"from": "n-cw", "to": "n-lambda", "label": "metrics"}),
    ]
    return Architecture(
        id=str(uuid4()),
        name=name,
        nodes=nodes,
        edges=edges,
        source="sample",
        metadata={"region": region, "pattern": "serverless-web"},
    )


def build_architecture_from_requirements(requirements: Requirements) -> Architecture:
    """Deterministic mock generation based on requirements (no AWS calls)."""
    region = requirements.region
    nodes: list[ArchitectureNode] = []
    edges: list[ArchitectureEdge] = []

    def add(node: ArchitectureNode) -> None:
        nodes.append(node)

    # Always include observability + IAM
    add(
        ArchitectureNode(
            id="n-iam",
            service_id="iam",
            label="IAM Roles",
            props={"wildcard_actions": False},
            x=600,
            y=40,
        )
    )
    add(
        ArchitectureNode(
            id="n-cw",
            service_id="cloudwatch",
            label="CloudWatch",
            props={"alarms": True},
            x=600,
            y=200,
        )
    )

    if requirements.workload.value in ("web", "api"):
        add(
            ArchitectureNode(
                id="n-cf",
                service_id="cloudfront",
                label="CloudFront",
                props={},
                x=80,
                y=40,
            )
        )
        add(
            ArchitectureNode(
                id="n-s3",
                service_id="s3",
                label="Static/Content S3",
                props={
                    "encryption": "AES256",
                    "public": False,
                },
                x=80,
                y=200,
            )
        )
        add(
            ArchitectureNode(
                id="n-apigw",
                service_id="api_gateway",
                label="API Gateway",
                props={},
                x=280,
                y=40,
            )
        )
        add(
            ArchitectureNode(
                id="n-lambda",
                service_id="lambda",
                label="Business Logic",
                props={"runtime": "python3.12"},
                x=280,
                y=200,
            )
        )
        edges.extend(
            [
                ArchitectureEdge(id="e1", **{"from": "n-cf", "to": "n-s3", "label": "static"}),
                ArchitectureEdge(id="e2", **{"from": "n-cf", "to": "n-apigw", "label": "api"}),
                ArchitectureEdge(id="e3", **{"from": "n-apigw", "to": "n-lambda", "label": "invoke"}),
                ArchitectureEdge(id="e4", **{"from": "n-iam", "to": "n-lambda", "label": "role"}),
                ArchitectureEdge(id="e5", **{"from": "n-cw", "to": "n-lambda", "label": "logs"}),
            ]
        )

        if requirements.budget.lower() in ("low", "minimal", "constrained") or True:
            add(
                ArchitectureNode(
                    id="n-ddb",
                    service_id="dynamodb",
                    label="DynamoDB",
                    props={
                        "capacity_mode": "on-demand",
                        "encryption": True,
                        "pit_recovery": True,
                    },
                    x=480,
                    y=200,
                )
            )
            edges.append(
                ArchitectureEdge(id="e6", **{"from": "n-lambda", "to": "n-ddb", "label": "data"})
            )
        if requirements.availability.value in ("high", "critical"):
            add(
                ArchitectureNode(
                    id="n-vpc",
                    service_id="vpc",
                    label="VPC",
                    props={"multi_az": True},
                    x=280,
                    y=360,
                )
            )
            edges.append(
                ArchitectureEdge(id="e7", **{"from": "n-lambda", "to": "n-vpc", "label": "network"})
            )
        if requirements.data_sensitivity.value in ("confidential", "regulated"):
            add(
                ArchitectureNode(
                    id="n-kms",
                    service_id="kms",
                    label="KMS",
                    props={},
                    x=480,
                    y=40,
                )
            )
            add(
                ArchitectureNode(
                    id="n-waf",
                    service_id="waf",
                    label="WAF",
                    props={},
                    x=80,
                    y=360,
                )
            )
            edges.append(
                ArchitectureEdge(id="e8", **{"from": "n-waf", "to": "n-cf", "label": "protect"})
            )

    elif requirements.workload.value == "batch":
        add(
            ArchitectureNode(
                id="n-sfn",
                service_id="step_functions",
                label="Step Functions",
                props={},
                x=200,
                y=80,
            )
        )
        add(
            ArchitectureNode(
                id="n-lambda",
                service_id="lambda",
                label="Workers",
                props={},
                x=200,
                y=220,
            )
        )
        add(
            ArchitectureNode(
                id="n-sqs",
                service_id="sqs",
                label="Work Queue",
                props={},
                x=400,
                y=220,
            )
        )
        add(
            ArchitectureNode(
                id="n-s3",
                service_id="s3",
                label="Input/Output Bucket",
                props={"encryption": "AES256", "public": False},
                x=400,
                y=80,
            )
        )
        edges.extend(
            [
                ArchitectureEdge(id="e1", **{"from": "n-sfn", "to": "n-lambda", "label": "orchestrate"}),
                ArchitectureEdge(id="e2", **{"from": "n-lambda", "to": "n-sqs", "label": "queue"}),
                ArchitectureEdge(id="e3", **{"from": "n-lambda", "to": "n-s3", "label": "io"}),
                ArchitectureEdge(id="e4", **{"from": "n-iam", "to": "n-lambda", "label": "role"}),
                ArchitectureEdge(id="e5", **{"from": "n-cw", "to": "n-sfn", "label": "metrics"}),
            ]
        )
    else:
        # Generic API-ish fallback
        return build_sample_web_architecture(
            name=f"Generated: {requirements.purpose[:40]}",
            region=region,
        )

    return Architecture(
        id=str(uuid4()),
        name=f"Generated: {requirements.purpose[:48]}",
        nodes=nodes,
        edges=edges,
        source="generated",
        metadata={"region": region, "demo": True},
    )


class ArchitecturePlanner:
    """Plans architectures using Bedrock when available, else deterministic mock."""

    def __init__(self, bedrock_client: Any = None) -> None:
        self.bedrock = bedrock_client

    def generate(
        self,
        requirements: Requirements,
        clarification_answers: Optional[Dict[str, str]] = None,
    ) -> Architecture:
        clarification_answers = clarification_answers or {}
        if self.bedrock is not None:
            try:
                result = self.bedrock.generate_architecture(
                    requirements.model_dump(),
                    clarification_answers,
                )
                if isinstance(result, Architecture):
                    return result
                if isinstance(result, dict):
                    return Architecture.model_validate(result)
            except Exception:
                pass
        return build_architecture_from_requirements(requirements)
