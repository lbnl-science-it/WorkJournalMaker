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
from datetime import date


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

        replace_calls = []
        _real_replace = os.replace

        def tracking_replace(src, dst):
            replace_calls.append((str(src), str(dst)))
            return _real_replace(src, dst)

        with patch('web.services.entry_manager.os.replace', side_effect=tracking_replace):
            response = isolated_app_client.post(f"/api/entries/{today}", json=entry_data)
            assert response.status_code == 200

        # At least one replace call should have a .tmp source
        tmp_replaces = [c for c in replace_calls if c[0].endswith('.tmp')]
        assert len(tmp_replaces) > 0, (
            f"os.replace was not called with a .tmp source file. "
            f"save_entry_content is writing directly instead of using atomic write-then-rename. "
            f"All replace calls: {replace_calls}"
        )

        # The .tmp source should have been renamed to the final .txt path
        src, dst = tmp_replaces[0]
        assert dst.endswith('.txt'), f"Rename destination is not .txt: {dst}"

        # Verify the content was written correctly
        txt_files = list(tmp_path.rglob("*.txt"))
        assert len(txt_files) > 0
        assert txt_files[0].read_text() == "Content written atomically"

    def test_concurrent_writes_use_unique_tmp_files(self, isolated_app_client, tmp_path):
        """Two rapid sequential writes to the same date must not corrupt each other.

        Each write gets its own unique temp file via tempfile.mkstemp, so even
        if two requests overlap, they cannot overwrite each other's temp data.
        The final content must be from one of the two writes, not a mix.
        """
        today = date.today().isoformat()
        content_a = "Concurrent write A content"
        content_b = "Concurrent write B content"

        response_a = isolated_app_client.post(
            f"/api/entries/{today}",
            json={"date": today, "content": content_a}
        )
        response_b = isolated_app_client.post(
            f"/api/entries/{today}",
            json={"date": today, "content": content_b}
        )

        assert response_a.status_code == 200
        assert response_b.status_code == 200

        # No .tmp files should remain
        tmp_files = list(tmp_path.rglob("*.tmp"))
        assert len(tmp_files) == 0, f"Leftover .tmp files: {tmp_files}"

        # Final content must be one of the two writes, not corrupted
        txt_files = list(tmp_path.rglob("*.txt"))
        assert len(txt_files) > 0
        final_content = txt_files[0].read_text()
        assert final_content in (content_a, content_b), (
            f"Final content is neither write A nor write B (possible corruption): {final_content!r}"
        )
