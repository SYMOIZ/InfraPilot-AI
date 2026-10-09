"""Parse draw.io / mxGraph XML into Architecture models."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET

from app.models.schemas import Architecture, ArchitectureEdge, ArchitectureNode
from app.models.validation import load_catalog_service_ids


# Map keywords in style/value to catalog service_ids
SERVICE_HINTS: List[Tuple[str, str]] = [
    ("cloudfront", "cloudfront"),
    ("api_gateway", "api_gateway"),
    ("api gateway", "api_gateway"),
    ("dynamodb", "dynamodb"),
    ("lambda", "lambda"),
    ("step_functions", "step_functions"),
    ("step functions", "step_functions"),
    ("secrets_manager", "secrets_manager"),
    ("cloudwatch", "cloudwatch"),
    ("cognito", "cognito"),
    ("application_load_balancer", "alb"),
    ("load balancer", "alb"),
    ("alb", "alb"),
    ("rds", "rds"),
    ("s3", "s3"),
    ("ec2", "ec2"),
    ("vpc", "vpc"),
    ("iam", "iam"),
    ("sqs", "sqs"),
    ("sns", "sns"),
    ("ecs", "ecs"),
    ("eks", "eks"),
    ("waf", "waf"),
    ("kms", "kms"),
]


class DrawioParseError(ValueError):
    """Raised when draw.io XML cannot be parsed."""


def _guess_service_id(value: str, style: str) -> str:
    blob = f"{value} {style}".lower()
    for hint, service_id in SERVICE_HINTS:
        if hint in blob:
            return service_id
    # Fallback: sanitize value
    cleaned = re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")
    catalog = load_catalog_service_ids()
    if cleaned in catalog:
        return cleaned
    return "ec2"  # generic placeholder when unknown


def _cell_is_vertex(cell: Element) -> bool:
    return cell.get("vertex") == "1"


def _cell_is_edge(cell: Element) -> bool:
    return cell.get("edge") == "1"


def parse_drawio_xml(xml_content: str) -> Architecture:
    """Extract nodes and edges from draw.io XML."""
    if not xml_content or not xml_content.strip():
        raise DrawioParseError("Empty draw.io content")

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise DrawioParseError(f"Malformed draw.io XML: {exc}") from exc

    # Support mxfile > diagram > mxGraphModel > root > mxCell
    cells: List[Element] = []
    if root.tag.endswith("mxfile") or root.tag == "mxfile":
        for cell in root.iter():
            if cell.tag.endswith("mxCell") or cell.tag == "mxCell":
                cells.append(cell)
    else:
        for cell in root.iter():
            if cell.tag.endswith("mxCell") or cell.tag == "mxCell":
                cells.append(cell)

    if not cells:
        raise DrawioParseError("No mxCell elements found in draw.io XML")

    nodes: List[ArchitectureNode] = []
    edges: List[ArchitectureEdge] = []
    id_map: Dict[str, str] = {}

    for cell in cells:
        cid = cell.get("id")
        if cid in (None, "0", "1"):
            continue
        if _cell_is_vertex(cell):
            value = cell.get("value") or cid
            # Strip simple HTML
            value = re.sub(r"<[^>]+>", "", value).strip() or cid
            style = cell.get("style") or ""
            service_id = _guess_service_id(value, style)
            x = y = None
            geom = None
            for child in list(cell):
                if child.tag.endswith("mxGeometry") or child.tag == "mxGeometry":
                    geom = child
                    break
            if geom is not None:
                try:
                    x = float(geom.get("x") or 0)
                    y = float(geom.get("y") or 0)
                except ValueError:
                    x = y = None
            node = ArchitectureNode(
                id=cid,
                service_id=service_id,
                label=value,
                props={},
                x=x,
                y=y,
            )
            nodes.append(node)
            id_map[cid] = cid
        elif _cell_is_edge(cell):
            source = cell.get("source")
            target = cell.get("target")
            if not source or not target:
                continue
            label = cell.get("value") or None
            if label:
                label = re.sub(r"<[^>]+>", "", label).strip() or None
            edges.append(
                ArchitectureEdge(
                    id=cid,
                    **{"from": source, "to": target, "label": label},
                )
            )

    if not nodes:
        raise DrawioParseError("No vertex mxCell nodes found")

    # Drop edges referencing missing nodes
    node_ids = {n.id for n in nodes}
    edges = [e for e in edges if e.from_node in node_ids and e.to_node in node_ids]

    return Architecture(
        name="Uploaded Architecture",
        nodes=nodes,
        edges=edges,
        source="uploaded",
        metadata={"parser": "drawio"},
    )


def validate_drawio_xml(xml_content: str) -> Tuple[bool, Optional[str]]:
    try:
        parse_drawio_xml(xml_content)
        return True, None
    except DrawioParseError as exc:
        return False, str(exc)
