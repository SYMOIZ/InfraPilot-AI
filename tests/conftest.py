"""Pytest fixtures for InfraPilot AI."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Force demo mode before importing app
os.environ["DEMO_MODE"] = "true"
os.environ.pop("AWS_ACCESS_KEY_ID", None)
os.environ.pop("AWS_SECRET_ACCESS_KEY", None)

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

for path in (str(REPO_ROOT), str(BACKEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

# Isolate local data per test session
os.environ["LOCAL_DATA_DIR"] = str(REPO_ROOT / ".test_data")


@pytest.fixture(autouse=True)
def _reset_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path / "data"))
    from app.config import get_settings
    from app.dependencies import reset_singletons

    get_settings.cache_clear()
    reset_singletons()
    yield
    reset_singletons()
    get_settings.cache_clear()


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_requirements_dict():
    return json.loads((FIXTURES / "sample_requirements.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_architecture_dict():
    return json.loads((FIXTURES / "sample_architecture.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_drawio_xml():
    return (FIXTURES / "sample_drawio.xml").read_text(encoding="utf-8")


@pytest.fixture
def malformed_drawio_xml():
    return (FIXTURES / "malformed_drawio.xml").read_text(encoding="utf-8")


@pytest.fixture
def sample_requirements(sample_requirements_dict):
    from app.models.schemas import Requirements

    return Requirements.model_validate(sample_requirements_dict)


@pytest.fixture
def sample_architecture(sample_architecture_dict):
    from app.models.schemas import Architecture

    return Architecture.model_validate(sample_architecture_dict)
