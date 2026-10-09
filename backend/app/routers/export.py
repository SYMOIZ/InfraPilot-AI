"""Export endpoints for drawio, png, and excel."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.dependencies import get_project_or_404
from app.services import exporter

router = APIRouter(prefix="/projects", tags=["export"])


@router.get("/{project_id}/export/drawio")
def export_drawio(project_id: str) -> Response:
    project = get_project_or_404(project_id)
    architecture = project.optimized_architecture or project.architecture
    if architecture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No architecture available to export",
        )
    content = exporter.export_drawio(architecture)
    return Response(
        content=content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{project_id}.drawio"'
        },
    )


@router.get("/{project_id}/export/png")
def export_png(project_id: str) -> Response:
    project = get_project_or_404(project_id)
    architecture = project.optimized_architecture or project.architecture
    if architecture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No architecture available to export",
        )
    try:
        content = exporter.export_png(architecture)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "PNG export unavailable. Use /export/drawio for an editable diagram. "
                f"Reason: {exc}"
            ),
        ) from exc
    return Response(
        content=content,
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{project_id}.png"',
            "X-InfraPilot-Note": (
                "Placeholder PNG via Pillow - not full draw.io fidelity"
            ),
        },
    )


@router.get("/{project_id}/export/excel")
def export_excel(project_id: str) -> Response:
    project = get_project_or_404(project_id)
    if project.architecture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No architecture available to export",
        )
    content = exporter.export_excel(project)
    return Response(
        content=content,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{project_id}.xlsx"'
        },
    )
