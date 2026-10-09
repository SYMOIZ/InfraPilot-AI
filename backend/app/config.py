"""Application configuration via environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for InfraPilot AI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    demo_mode: bool = False
    force_local_storage: bool = False
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "amazon.nova-micro-v1:0"
    bedrock_region: str | None = None
    s3_bucket: str | None = None
    dynamodb_table: str | None = None
    local_data_dir: str = "data"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def effective_bedrock_region(self) -> str:
        return self.bedrock_region or self.aws_region

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def local_data_path(self) -> Path:
        path = Path(self.local_data_dir)
        if not path.is_absolute():
            # Lambda only allows writes under /tmp; use it when detected.
            import os

            if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
                path = Path("/tmp") / "infrapilot" / path.name
            else:
                # Resolve relative to backend directory when possible
                backend_root = Path(__file__).resolve().parent.parent
                path = backend_root / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def is_demo(self) -> bool:
        """True when DEMO_MODE is set or AWS credentials are unavailable."""
        if self.demo_mode:
            return True
        import os

        return not (
            os.environ.get("AWS_ACCESS_KEY_ID")
            or os.environ.get("AWS_PROFILE")
            or os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
            or os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE")
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
