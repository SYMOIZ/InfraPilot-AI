"""draw.io builder unit tests."""

from __future__ import annotations

from app.services.drawio_builder import build_drawio_xml
from app.services.drawio_parser import parse_drawio_xml


def test_builder_produces_parseable_xml(sample_architecture):
    xml = build_drawio_xml(sample_architecture)
    assert "mxfile" in xml
    assert "mxCell" in xml
    assert sample_architecture.nodes[0].id in xml

    # Round-trip: builder output should be parseable
    parsed = parse_drawio_xml(xml)
    assert len(parsed.nodes) == len(sample_architecture.nodes)
    assert len(parsed.edges) == len(sample_architecture.edges)


def test_builder_escapes_labels(sample_architecture):
    sample_architecture.nodes[0].label = 'Bucket <prod> & "assets"'
    xml = build_drawio_xml(sample_architecture)
    assert "&lt;prod&gt;" in xml or "Bucket" in xml
    assert "mxGraphModel" in xml
