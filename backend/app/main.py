"""InfraPilot AI FastAPI application."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure repo-root packages (agent, rules, catalog) are importable
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
for path in (_REPO_ROOT, _BACKEND_ROOT, str(_REPO_ROOT)):
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)

from app.config import get_settings  # noqa: E402
from app.routers import (  # noqa: E402
    architecture,
    demo,
    evaluation,
    export,
    optimization,
    projects,
    requirements,
    upload,
)

settings = get_settings()

app = FastAPI(
    title="InfraPilot AI",
    description=(
        "AI-powered AWS architecture design, evaluation, gap analysis, "
        "and optimization. Does not deploy infrastructure or generate "
        "Terraform/CloudFormation."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(demo.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(requirements.router, prefix=API_PREFIX)
app.include_router(architecture.router, prefix=API_PREFIX)
app.include_router(evaluation.router, prefix=API_PREFIX)
app.include_router(optimization.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(upload.router, prefix=API_PREFIX)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "InfraPilot AI",
        "demo_mode": settings.is_demo(),
        "version": "0.1.0",
    }


@app.get("/")
def root() -> dict:
    return {
        "service": "InfraPilot AI",
        "docs": "/docs",
        "health": "/health",
        "api": API_PREFIX,
    }
