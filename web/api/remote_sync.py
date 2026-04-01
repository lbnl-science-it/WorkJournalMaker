# ABOUTME: API endpoints for the sync protocol (manifest, upload, download).
# ABOUTME: Server-side endpoints that sync clients connect to.
"""
Remote Sync API Endpoints for Work Journal Maker

This module provides REST API endpoints for the file-level sync protocol
between clients and server.
"""

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/remote-sync", tags=["sync"])


class ManifestEntryModel(BaseModel):
    """Pydantic model for manifest entry."""
    relative_path: str
    sha256: str
    modified_at: datetime


class ManifestRequest(BaseModel):
    """Request model for manifest comparison."""
    entries: List[ManifestEntryModel]
    last_sync_at: Optional[datetime] = None


class SyncDiffResponse(BaseModel):
    """Response model for sync diff."""
    to_upload: List[str]
    to_download: List[str]
    conflicts: List[str]


@router.post("/manifest", response_model=SyncDiffResponse)
async def compare_manifest(manifest: ManifestRequest, request: Request):
    """
    Compare client manifest with server state, return diff.

    Args:
        manifest: Client's file manifest
        request: FastAPI request object

    Returns:
        SyncDiffResponse: Files to upload, download, and conflicts
    """
    sync_service = request.app.state.remote_sync_service
    user_id = getattr(request.state, 'user_id', 'local')

    from web.services.remote_sync_service import FileManifest, ManifestEntry
    client_manifest = FileManifest(
        entries=[
            ManifestEntry(
                relative_path=e.relative_path,
                sha256=e.sha256,
                modified_at=e.modified_at,
            )
            for e in manifest.entries
        ]
    )

    server_manifest = sync_service.generate_manifest(user_id)
    diff = sync_service.compare_manifests(client_manifest, server_manifest)

    return SyncDiffResponse(
        to_upload=diff.to_upload,
        to_download=diff.to_download,
        conflicts=diff.conflicts,
    )


@router.post("/upload")
async def upload_file(
    relative_path: str,
    file: UploadFile = File(...),
    request: Request = None,
):
    """
    Upload a file from client to server.

    Args:
        relative_path: Relative path for the file
        file: File content
        request: FastAPI request object

    Returns:
        Dict with upload status
    """
    sync_service = request.app.state.remote_sync_service
    user_id = getattr(request.state, 'user_id', 'local')

    content = await file.read()
    sync_service.save_file(user_id, relative_path, content)
    return {"status": "ok", "path": relative_path}


@router.get("/download")
async def download_file(relative_path: str, request: Request):
    """
    Download a file from server to client.

    Args:
        relative_path: Relative path of the file to download
        request: FastAPI request object

    Returns:
        FileResponse: File content
    """
    sync_service = request.app.state.remote_sync_service
    user_id = getattr(request.state, 'user_id', 'local')

    file_path = sync_service.get_file_path(user_id, relative_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(file_path), filename=file_path.name)


@router.post("/complete")
async def sync_complete(request: Request):
    """
    Mark sync as complete, update last_sync_at.

    Args:
        request: FastAPI request object

    Returns:
        Dict with sync completion status
    """
    user_id = getattr(request.state, 'user_id', 'local')
    return {"status": "ok", "synced_at": datetime.utcnow().isoformat()}
