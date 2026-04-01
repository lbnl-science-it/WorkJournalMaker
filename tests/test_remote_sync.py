# ABOUTME: Tests for remote sync service and API endpoints.
# ABOUTME: Covers manifest generation, comparison, and file-level sync operations.
"""Tests for remote sync service and API."""
import pytest
from datetime import date, datetime
from pathlib import Path


class TestManifestGeneration:
    def test_generate_manifest_from_files(self, tmp_path):
        """Generate manifest from a directory of journal files."""
        from web.services.remote_sync_service import RemoteSyncService

        # Create sample files
        journal_dir = tmp_path / "worklogs"
        journal_dir.mkdir()
        file1 = journal_dir / "worklog_2024-01-15.txt"
        file1.write_text("Today I worked on X.")
        file2 = journal_dir / "worklog_2024-01-16.txt"
        file2.write_text("Today I worked on Y.")

        service = RemoteSyncService(storage_root=str(tmp_path))
        manifest = service.generate_manifest(user_id="local")

        assert len(manifest.entries) == 2
        from web.services.remote_sync_service import ManifestEntry
        assert all(isinstance(e, ManifestEntry) for e in manifest.entries)

    def test_manifest_entry_has_hash(self, tmp_path):
        """Each manifest entry includes a SHA256 hash."""
        from web.services.remote_sync_service import RemoteSyncService

        journal_dir = tmp_path / "worklogs"
        journal_dir.mkdir()
        file1 = journal_dir / "worklog_2024-01-15.txt"
        file1.write_text("Today I worked on X.")

        service = RemoteSyncService(storage_root=str(tmp_path))
        manifest = service.generate_manifest(user_id="local")

        entry = manifest.entries[0]
        assert entry.sha256 is not None
        assert len(entry.sha256) == 64  # SHA256 hex digest length


class TestManifestComparison:
    def test_compare_identical_manifests(self):
        """Identical manifests produce no diff."""
        from web.services.remote_sync_service import (
            RemoteSyncService, FileManifest, ManifestEntry
        )

        entries = [
            ManifestEntry(
                relative_path="worklog_2024-01-15.txt",
                sha256="abc123" * 10 + "abcd",
                modified_at=datetime(2024, 1, 15, 12, 0),
            )
        ]
        client_manifest = FileManifest(entries=entries)
        server_manifest = FileManifest(entries=entries)

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(client_manifest, server_manifest)

        assert len(diff.to_upload) == 0
        assert len(diff.to_download) == 0

    def test_client_has_new_file(self):
        """File on client but not server → to_upload."""
        from web.services.remote_sync_service import (
            RemoteSyncService, FileManifest, ManifestEntry
        )

        client_entries = [
            ManifestEntry(
                relative_path="worklog_2024-01-15.txt",
                sha256="abc123" * 10 + "abcd",
                modified_at=datetime(2024, 1, 15, 12, 0),
            )
        ]
        client_manifest = FileManifest(entries=client_entries)
        server_manifest = FileManifest(entries=[])

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(client_manifest, server_manifest)

        assert len(diff.to_upload) == 1
        assert diff.to_upload[0] == "worklog_2024-01-15.txt"

    def test_server_has_new_file(self):
        """File on server but not client → to_download."""
        from web.services.remote_sync_service import (
            RemoteSyncService, FileManifest, ManifestEntry
        )

        server_entries = [
            ManifestEntry(
                relative_path="worklog_2024-01-16.txt",
                sha256="def456" * 10 + "defg",
                modified_at=datetime(2024, 1, 16, 12, 0),
            )
        ]
        client_manifest = FileManifest(entries=[])
        server_manifest = FileManifest(entries=server_entries)

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(client_manifest, server_manifest)

        assert len(diff.to_download) == 1
        assert diff.to_download[0] == "worklog_2024-01-16.txt"

    def test_conflict_last_write_wins(self):
        """Same file modified on both sides → last-write-wins."""
        from web.services.remote_sync_service import (
            RemoteSyncService, FileManifest, ManifestEntry
        )

        client_entry = ManifestEntry(
            relative_path="worklog_2024-01-15.txt",
            sha256="client_hash_" + "x" * 52,
            modified_at=datetime(2024, 1, 15, 14, 0),  # newer
        )
        server_entry = ManifestEntry(
            relative_path="worklog_2024-01-15.txt",
            sha256="server_hash_" + "y" * 52,
            modified_at=datetime(2024, 1, 15, 12, 0),  # older
        )

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(
            FileManifest(entries=[client_entry]),
            FileManifest(entries=[server_entry]),
        )

        # Client is newer → upload to server
        assert len(diff.to_upload) == 1
        assert len(diff.conflicts) == 1


class TestPathTraversal:
    def test_save_file_rejects_path_escape(self, tmp_path):
        """save_file rejects relative paths that escape user storage."""
        from web.services.remote_sync_service import RemoteSyncService

        service = RemoteSyncService(storage_root=str(tmp_path))
        with pytest.raises(ValueError, match="Path escapes user storage"):
            service.save_file("local", "../../etc/passwd", b"malicious")

    def test_get_file_path_rejects_path_escape(self, tmp_path):
        """get_file_path rejects relative paths that escape user storage."""
        from web.services.remote_sync_service import RemoteSyncService

        service = RemoteSyncService(storage_root=str(tmp_path))
        with pytest.raises(ValueError, match="Path escapes user storage"):
            service.get_file_path("local", "../../../etc/shadow")

    def test_save_file_allows_valid_subpath(self, tmp_path):
        """save_file accepts valid relative paths within storage."""
        from web.services.remote_sync_service import RemoteSyncService

        service = RemoteSyncService(storage_root=str(tmp_path))
        result = service.save_file("local", "worklogs/worklog_2024-01-15.txt", b"content")
        assert result.exists()
        assert result.read_bytes() == b"content"
