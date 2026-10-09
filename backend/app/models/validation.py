"""Validation helpers for architectures, requirements, and catalog IDs."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Set, Tuple

from app.models.schemas import Architecture, Requirements


def _catalog_path() -> Path:
    # repo_root/catalog/aws_services.json
    return Path(__file__).resolve().parents[3] / "catalog" / "aws_services.json"


@lru_cache
def load_catalog_service_ids() -> Set[str]:
    path = _catalog_path()
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {s["id"] for s in data.get("services", [])}


@lru_cache
def load_catalog() -> dict:
    path = _catalog_path()
    if not path.exists():
        return {"services": []}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_architecture(architecture: Architecture) -> Tuple[bool, List[str]]:
    """Validate architecture graph integrity and catalog references."""
    errors: List[str] = []
    catalog_ids = load_catalog_service_ids()
    node_ids = {n.id for n in architecture.nodes}

    if not architecture.nodes:
        errors.append("Architecture must contain at least one node")

    seen: Set[str] = set()
    for node in architecture.nodes:
        if node.id in seen:
            errors.append(f"Duplicate node id: {node.id}")
        seen.add(node.id)
        if catalog_ids and node.service_id not in catalog_ids:
            errors.append(
                f"Unknown service_id '{node.service_id}' on node '{node.id}'"
            )
        if not node.label:
            errors.append(f"Node '{node.id}' is missing a label")

    for edge in architecture.edges:
        if edge.from_node not in node_ids:
            errors.append(
                f"Edge from '{edge.from_node}' references missing node"
            )
        if edge.to_node not in node_ids:
            errors.append(f"Edge to '{edge.to_node}' references missing node")

    return len(errors) == 0, errors


def validate_requirements(requirements: Requirements) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not requirements.purpose or not requirements.purpose.strip():
        errors.append("Purpose is required")
    if not requirements.region:
        errors.append("Region is required")
    return len(errors) == 0, errors


def service_ids_in_architecture(architecture: Architecture) -> Set[str]:
    return {n.service_id for n in architecture.nodes}
