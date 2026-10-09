"""draw.io parser unit tests."""

from __future__ import annotations

import pytest

from app.services.drawio_parser import DrawioParseError, parse_drawio_xml, validate_drawio_xml


def test_parse_sample_drawio(sample_drawio_xml):
    arch = parse_drawio_xml(sample_drawio_xml)
    assert len(arch.nodes) >= 4
    service_ids = {n.service_id for n in arch.nodes}
    assert "cloudfront" in service_ids
    assert "lambda" in service_ids
    assert "dynamodb" in service_ids
    assert "s3" in service_ids
    assert len(arch.edges) >= 3
    assert arch.source == "uploaded"


def test_malformed_drawio_raises(malformed_drawio_xml):
    with pytest.raises(DrawioParseError):
        parse_drawio_xml(malformed_drawio_xml)


def test_empty_drawio_raises():
    with pytest.raises(DrawioParseError):
        parse_drawio_xml("")


def test_validate_helpers(sample_drawio_xml, malformed_drawio_xml):
    ok, err = validate_drawio_xml(sample_drawio_xml)
    assert ok
    assert err is None
    ok2, err2 = validate_drawio_xml(malformed_drawio_xml)
    assert not ok2
    assert err2
