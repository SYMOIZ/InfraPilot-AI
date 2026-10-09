"""Bedrock client mock / demo mode tests."""

from __future__ import annotations

import os

from app.config import Settings
from app.services.bedrock_client import BedrockClient
from app.models.schemas import RuleStatus


def test_demo_mode_generate_architecture(sample_requirements_dict):
    settings = Settings(demo_mode=True)
    client = BedrockClient(settings)
    assert client.demo is True
    arch = client.generate_architecture(sample_requirements_dict)
    assert arch.nodes
    assert arch.source in ("generated", "sample")


def test_demo_mode_analyze_gaps_unknown_not_pass(sample_architecture_dict):
    settings = Settings(demo_mode=True)
    client = BedrockClient(settings)
    # Strip cloudwatch to force unknown/warning
    sample_architecture_dict = {
        **sample_architecture_dict,
        "nodes": [
            n
            for n in sample_architecture_dict["nodes"]
            if n["service_id"] != "cloudwatch"
        ],
        "edges": [],
    }
    findings = client.analyze_gaps(
        sample_architecture_dict,
        {"workload": "web"},
    )
    assert findings
    assert all(f.status != RuleStatus.PASS or f.rule_id != "MOCK-GAP-001" for f in findings)
    assert any(f.status in (RuleStatus.UNKNOWN, RuleStatus.WARNING) for f in findings)


def test_is_demo_without_credentials(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", raising=False)
    monkeypatch.delenv("AWS_WEB_IDENTITY_TOKEN_FILE", raising=False)
    monkeypatch.setenv("DEMO_MODE", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    settings = Settings(demo_mode=False)
    assert settings.is_demo() is True
