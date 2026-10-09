"""Build editable draw.io XML from Architecture models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional
from xml.sax.saxutils import escape

from app.models.schemas import Architecture
from app.models.validation import load_catalog


def _styles_from_catalog() -> Dict[str, str]:
    catalog = load_catalog()
    return {
        s["id"]: s.get(
            "drawio_style",
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;",
        )
        for s in catalog.get("services", [])
    }


DEFAULT_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
)


def build_drawio_xml(architecture: Architecture) -> str:
    """Generate valid mxfile XML for diagrams.net / draw.io."""
    styles = _styles_from_catalog()
    cells: list[str] = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
    ]

    for idx, node in enumerate(architecture.nodes):
        x = node.x if node.x is not None else 40 + (idx % 4) * 180
        y = node.y if node.y is not None else 40 + (idx // 4) * 140
        style = styles.get(node.service_id, DEFAULT_STYLE)
        label = escape(node.label)
        cells.append(
            f'<mxCell id="{escape(node.id)}" value="{label}" style="{escape(style)}" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="120" height="80" as="geometry"/>'
            f"</mxCell>"
        )

    for idx, edge in enumerate(architecture.edges):
        eid = edge.id or f"edge-{idx}"
        label = escape(edge.label) if edge.label else ""
        cells.append(
            f'<mxCell id="{escape(eid)}" value="{label}" '
            f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;'
            f'jettySize=auto;html=1;" edge="1" parent="1" '
            f'source="{escape(edge.from_node)}" target="{escape(edge.to_node)}">'
            f'<mxGeometry relative="1" as="geometry"/>'
            f"</mxCell>"
        )

    inner = "\n        ".join(cells)
    diagram_name = escape(architecture.name or "Architecture")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="InfraPilot AI" agent="InfraPilot" version="22.1.0">
  <diagram id="infrapilot" name="{diagram_name}">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        {inner}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""
    return xml


def architecture_to_drawio_file(architecture: Architecture, path: Path) -> Path:
    path.write_text(build_drawio_xml(architecture), encoding="utf-8")
    return path
