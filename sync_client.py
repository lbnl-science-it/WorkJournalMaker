# ABOUTME: HTTP client for syncing local journal files with a remote server
# ABOUTME: Implements the manifest-compare-upload-download sync protocol

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List

import requests

from web.services.remote_sync_service import FileManifest, ManifestEntry, SyncDiff


class SyncClient:
    """Client for syncing local journal files with a remote server."""

    def __init__(
        self,
        remote_url: str,
        auth_token: str,
        local_root: str,
        timeout: int = 30,
    ):
        self.remote_url = remote_url.rstrip("/")
        self.auth_token = auth_token
        self.local_root = Path(local_root)
        self.timeout = timeout

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers with authentication."""
        return {
            "X-API-Key": self.auth_token,
            "User-Agent": "WorkJournalMaker-SyncClient/1.0",
        }

    def generate_local_manifest(self) -> FileManifest:
        """Generate manifest from local journal files."""
        entries = []
        for root, _dirs, files in os.walk(self.local_root):
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                file_path = Path(root) / filename
                relative = file_path.relative_to(self.local_root)
                content = file_path.read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                modified_at = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                entries.append(ManifestEntry(
                    relative_path=str(relative),
                    sha256=sha256,
                    modified_at=modified_at,
                ))
        return FileManifest(entries=entries)

    def sync(self) -> Dict[str, int]:
        """Execute full sync cycle: manifest → upload → download → complete."""
        # Step 1: Generate local manifest and send to server
        local_manifest = self.generate_local_manifest()
        diff = self._send_manifest(local_manifest)

        uploaded = 0
        downloaded = 0

        # Step 2: Upload files server needs
        for path in diff.get("to_upload", []):
            self._upload_file(path)
            uploaded += 1

        # Step 3: Download files we need
        for path in diff.get("to_download", []):
            self._download_file(path)
            downloaded += 1

        # Step 4: Mark sync complete
        self._complete_sync()

        return {
            "uploaded": uploaded,
            "downloaded": downloaded,
            "conflicts": len(diff.get("conflicts", [])),
        }

    def _send_manifest(self, manifest: FileManifest) -> dict:
        """Send local manifest to server, get back diff."""
        payload = {
            "entries": [
                {
                    "relative_path": e.relative_path,
                    "sha256": e.sha256,
                    "modified_at": e.modified_at.isoformat(),
                }
                for e in manifest.entries
            ]
        }
        response = requests.post(
            f"{self.remote_url}/api/remote-sync/manifest",
            json=payload,
            headers=self._build_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _upload_file(self, relative_path: str) -> None:
        """Upload a single file to the server."""
        file_path = self.local_root / relative_path
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.remote_url}/api/remote-sync/upload",
                params={"relative_path": relative_path},
                files={"file": (file_path.name, f)},
                headers=self._build_headers(),
                timeout=self.timeout,
            )
        response.raise_for_status()

    def _download_file(self, relative_path: str) -> None:
        """Download a single file from the server."""
        response = requests.get(
            f"{self.remote_url}/api/remote-sync/download",
            params={"relative_path": relative_path},
            headers=self._build_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()

        file_path = self.local_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(response.content)

    def _complete_sync(self) -> None:
        """Mark sync as complete on server."""
        response = requests.post(
            f"{self.remote_url}/api/remote-sync/complete",
            headers=self._build_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
