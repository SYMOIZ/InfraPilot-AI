"""File upload and draw.io extraction."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.dependencies import get_project_or_404, get_storage
from app.models.schemas import Project
from app.services.drawio_parser import DrawioParseError, parse_drawio_xml

router = APIRouter(prefix="/projects", tags=["upload"])

ALLOWED_EXTENSIONS = {".drawio", ".xml", ".png", ".jpg", ".jpeg"}


@router.post("/{project_id}/upload", response_model=Project)
async def upload_architecture(
    project_id: str,
    file: UploadFile = File(...),
) -> Project:
    project = get_project_or_404(project_id)
    filename = file.filename or "upload.bin"
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    storage = get_storage()
    location = storage.save_upload(project_id, filename, content)
    project.uploaded_files.append(location)

    if lower.endswith((".drawio", ".xml")):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="draw.io/xml must be UTF-8 text",
            ) from exc
        try:
            architecture = parse_drawio_xml(text)
        except DrawioParseError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        project.architecture = architecture
    else:
        # PNG/JPG stored for reference; extraction not claimed
        project.architecture = project.architecture  # unchanged
        # Attach note in metadata if architecture exists
        if project.architecture:
            project.architecture.metadata["upload_image"] = location
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Image uploads are stored for reference only. "
                    "Provide drawio/xml to extract architecture, or generate one first."
                ),
            )

    return storage.save_project(project)
