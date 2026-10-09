"""Optimization planner unit tests."""

from __future__ import annotations

from app.models.schemas import (
    Architecture,
    ArchitectureNode,
    DataSensitivity,
    Requirements,
    WorkloadType,
)
from agent.optimization_planner import OptimizationPlanner


def test_optimize_adds_cloudwatch():
    arch = Architecture(
        name="Sparse",
        nodes=[
            ArchitectureNode(id="l", service_id="lambda", label="Fn", props={}),
            ArchitectureNode(
                id="apigw",
                service_id="api_gateway",
                label="API",
                props={},
            ),
        ],
        edges=[],
    )
    req = Requirements(purpose="API", workload=WorkloadType.API)
    proposal = OptimizationPlanner().optimize("p1", arch, req)
    services = {n.service_id for n in proposal.optimized.nodes}
    assert "cloudwatch" in services
    assert proposal.changes
    assert "price" not in proposal.cost_notes.lower() or "invent" in proposal.cost_notes.lower()


def test_optimize_encrypts_public_s3():
    arch = Architecture(
        nodes=[
            ArchitectureNode(
                id="s3",
                service_id="s3",
                label="Open",
                props={"public": True, "encryption": False},
            ),
            ArchitectureNode(id="cw", service_id="cloudwatch", label="CW", props={}),
        ]
    )
    req = Requirements(
        purpose="web",
        workload=WorkloadType.WEB,
        data_sensitivity=DataSensitivity.CONFIDENTIAL,
    )
    proposal = OptimizationPlanner().optimize("p1", arch, req)
    s3 = next(n for n in proposal.optimized.nodes if n.service_id == "s3")
    assert s3.props.get("public") is False
    assert s3.props.get("encryption") not in (None, False, "", "none")
    assert "kms" in {n.service_id for n in proposal.optimized.nodes}


def test_diff_helper(sample_architecture):
    from copy import deepcopy

    optimized = deepcopy(sample_architecture)
    optimized.nodes.append(
        ArchitectureNode(id="new-kms", service_id="kms", label="KMS", props={})
    )
    changes = OptimizationPlanner.diff(sample_architecture, optimized)
    assert any(c.change_type == "add" and c.service_id == "kms" for c in changes)
