"""Schema and validation unit tests."""

from __future__ import annotations

import pytest

from app.models.schemas import (
    Architecture,
    ArchitectureEdge,
    ArchitectureNode,
    Requirements,
)
from app.models.validation import validate_architecture, validate_requirements


def test_requirements_roundtrip(sample_requirements_dict):
    req = Requirements.model_validate(sample_requirements_dict)
    assert req.workload.value == "web"
    assert req.region == "us-east-1"
    dumped = req.model_dump()
    assert dumped["purpose"]


def test_architecture_edges_alias(sample_architecture_dict):
    arch = Architecture.model_validate(sample_architecture_dict)
    assert arch.nodes
    assert arch.edges
    assert arch.edges[0].from_node == "n-waf"
    as_json = arch.model_dump(by_alias=True)
    assert "from" in as_json["edges"][0]
    assert "to" in as_json["edges"][0]


def test_validate_architecture_ok(sample_architecture):
    ok, errors = validate_architecture(sample_architecture)
    assert ok
    assert errors == []


def test_validate_architecture_unknown_service():
    arch = Architecture(
        nodes=[
            ArchitectureNode(
                id="n1", service_id="not_a_real_service", label="Bad"
            )
        ],
        edges=[],
    )
    ok, errors = validate_architecture(arch)
    assert not ok
    assert any("Unknown service_id" in e for e in errors)


def test_validate_architecture_broken_edge():
    arch = Architecture(
        nodes=[ArchitectureNode(id="n1", service_id="s3", label="S3")],
        edges=[ArchitectureEdge(**{"from": "n1", "to": "missing", "label": "x"})],
    )
    ok, errors = validate_architecture(arch)
    assert not ok


def test_validate_requirements_requires_purpose():
    req = Requirements(purpose="   ")
    ok, errors = validate_requirements(req)
    assert not ok
    assert any("Purpose" in e for e in errors)
