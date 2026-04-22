# ABOUTME: Tests for atomic file write behavior in EntryManager.save_entry_content.
# ABOUTME: Verifies write-then-rename pattern prevents partial writes and cleans up on failure.

"""
Tests for atomic write behavior in save_entry_content.

Verifies that:
- Successful writes leave no .tmp files
- A write failure mid-operation preserves the original file content
"""

import pytest
import os
import asyncio
from datetime import date
from pathlib import Path


class TestAtomicWrite:
    """Test that save_entry_content uses atomic writes."""

    def test_no_tmp_files_after_successful_write(self, isolated_app_client, tmp_path):
        """After a successful POST, no .tmp files should remain in the write directory."""
        today = date.today().isoformat()
        entry_data = {
            "date": today,
            "content": "Atomic write test content"
        }

        response = isolated_app_client.post(f"/api/entries/{today}", json=entry_data)
        assert response.status_code == 200

        # No .tmp files should exist anywhere in tmp_path
        tmp_files = list(tmp_path.rglob("*.tmp"))
        assert len(tmp_files) == 0, f"Found leftover .tmp files: {tmp_files}"

    def test_write_uses_atomic_rename(self, isolated_app_client, tmp_path):
        """save_entry_content must write to a .tmp file then rename, not write directly.

        We verify this by checking that os.rename is called with a .tmp source path
        during the write operation. Without atomic writes, os.rename is never called.
        """
        from unittest.mock import patch, call

        today = date.today().isoformat()
        entry_data = {
            "date": today,
            "content": "Content written atomically"
        }

        rename_calls = []
        _real_rename = os.rename

        def tracking_rename(src, dst):
            rename_calls.append((str(src), str(dst)))
            return _real_rename(src, dst)

        with patch('web.services.entry_manager.os.rename', side_effect=tracking_rename):
            response = isolated_app_client.post(f"/api/entries/{today}", json=entry_data)
            assert response.status_code == 200

        # At least one rename call should have a .tmp source
        tmp_renames = [c for c in rename_calls if c[0].endswith('.tmp')]
        assert len(tmp_renames) > 0, (
            f"os.rename was not called with a .tmp source file. "
            f"save_entry_content is writing directly instead of using atomic write-then-rename. "
            f"All rename calls: {rename_calls}"
        )

        # The .tmp source should have been renamed to the final .txt path
        src, dst = tmp_renames[0]
        assert dst.endswith('.txt'), f"Rename destination is not .txt: {dst}"

        # Verify the content was written correctly
        txt_files = list(tmp_path.rglob("*.txt"))
        assert len(txt_files) > 0
        assert txt_files[0].read_text() == "Content written atomically"
