# ABOUTME: Sync protocol logic for manifest comparison and file-level sync.
# ABOUTME: Handles manifest generation, diff computation, and conflict detection.
"""
Remote Sync Service for Work Journal Maker

This module implements the sync protocol logic for comparing file manifests
and determining sync actions between client and server.
"""

import hashlib
import os
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ManifestEntry:
    """Single file entry in a sync manifest."""
    relative_path: str
    sha256: str
    modified_at: datetime


@dataclass
class FileManifest:
    """Complete file manifest for sync comparison."""
    entries: List[ManifestEntry] = field(default_factory=list)


@dataclass
class SyncDiff:
    """Result of comparing two manifests."""
    to_upload: List[str] = field(default_factory=list)    # client → server
    to_download: List[str] = field(default_factory=list)  # server → client
    conflicts: List[str] = field(default_factory=list)    # modified on both


class RemoteSyncService:
    """Handles sync protocol logic."""

    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)

    def generate_manifest(self, user_id: str) -> FileManifest:
        """
        Generate file manifest for a user's journal files.

        Args:
            user_id: User identifier (or 'local' for local mode)

        Returns:
            FileManifest: Manifest containing all journal files with hashes
        """
        user_root = self.storage_root / user_id if user_id != "local" else self.storage_root
        entries = []

        for root, _dirs, files in os.walk(user_root):
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                file_path = Path(root) / filename
                relative = file_path.relative_to(user_root)

                content = file_path.read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)

                entries.append(ManifestEntry(
                    relative_path=str(relative),
                    sha256=sha256,
                    modified_at=modified_at,
                ))

        return FileManifest(entries=entries)

    def compare_manifests(
        self, client: FileManifest, server: FileManifest
    ) -> SyncDiff:
        """
        Compare client and server manifests to determine sync actions.

        Args:
            client: Client's file manifest
            server: Server's file manifest

        Returns:
            SyncDiff: Diff showing files to upload, download, and conflicts
        """
        client_map = {e.relative_path: e for e in client.entries}
        server_map = {e.relative_path: e for e in server.entries}

        diff = SyncDiff()

        # Files on client but not server → upload
        for path in client_map:
            if path not in server_map:
                diff.to_upload.append(path)

        # Files on server but not client → download
        for path in server_map:
            if path not in client_map:
                diff.to_download.append(path)

        # Files on both with different hashes → conflict (last-write-wins)
        for path in client_map:
            if path in server_map:
                c = client_map[path]
                s = server_map[path]
                if c.sha256 != s.sha256:
                    diff.conflicts.append(path)
                    if c.modified_at >= s.modified_at:
                        diff.to_upload.append(path)
                    else:
                        diff.to_download.append(path)

        return diff

    def save_file(self, user_id: str, relative_path: str, content: bytes) -> Path:
        """
        Save uploaded file to user's storage.

        Args:
            user_id: User identifier (or 'local' for local mode)
            relative_path: Relative path within user's storage
            content: File content as bytes

        Returns:
            Path: Absolute path to saved file
        """
        user_root = self.storage_root / user_id if user_id != "local" else self.storage_root
        file_path = user_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return file_path

    def get_file_path(self, user_id: str, relative_path: str) -> Path:
        """
        Get absolute path for a user's file.

        Args:
            user_id: User identifier (or 'local' for local mode)
            relative_path: Relative path within user's storage

        Returns:
            Path: Absolute path to the file
        """
        user_root = self.storage_root / user_id if user_id != "local" else self.storage_root
        return user_root / relative_path
