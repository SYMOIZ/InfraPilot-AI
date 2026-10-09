"""FastAPI dependency injection."""

from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException, status

from app.config import Settings, get_settings
from app.models.schemas import Project
from app.services.bedrock_client import BedrockClient
from app.services.storage import StorageService


@lru_cache
def get_storage() -> StorageService:
    return StorageService(get_settings())


@lru_cache
def get_bedrock() -> BedrockClient:
    return BedrockClient(get_settings())


def get_project_or_404(project_id: str) -> Project:
    storage = get_storage()
    project = storage.get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found",
        )
    return project


def reset_singletons() -> None:
    """Test helper to clear cached dependencies."""
    get_storage.cache_clear()
    get_bedrock.cache_clear()
    get_settings.cache_clear()
