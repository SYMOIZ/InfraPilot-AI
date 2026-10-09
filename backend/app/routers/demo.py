"""Labeled sample/demo data endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from agent.architecture_planner import build_sample_web_architecture
from app.models.schemas import Architecture, Requirements, WorkloadType

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/sample")
def get_sample_data() -> dict:
    """Return clearly labeled sample requirements + architecture."""
    requirements = Requirements(
        purpose="Simple public web application with authenticated API",
        workload=WorkloadType.WEB,
        traffic="medium",
        data_sensitivity="internal",
        availability="high",
        recovery="RPO < 1h",
        budget="moderate",
        region="us-east-1",
        scalability="moderate",
        constraints=["No on-prem", "Prefer serverless"],
        notes="SAMPLE DATA — for demos and local testing only.",
    )
    architecture: Architecture = build_sample_web_architecture(
        name="SAMPLE: Serverless Web App",
        region="us-east-1",
    )
    architecture.metadata["label"] = "SAMPLE"
    architecture.metadata["disclaimer"] = (
        "This is labeled sample data for InfraPilot demos. "
        "It does not represent a deployed customer environment."
    )
    return {
        "label": "SAMPLE",
        "disclaimer": (
            "Labeled sample data for local demo mode. "
            "InfraPilot does not deploy infrastructure."
        ),
        "requirements": requirements.model_dump(),
        "architecture": architecture.model_dump(by_alias=True),
    }
