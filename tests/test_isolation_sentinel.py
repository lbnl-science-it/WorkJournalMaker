# ABOUTME: Sentinel test verifying that test isolation redirects file writes to tmp_path.
# ABOUTME: Guards against test suites accidentally writing to real worklog files.

"""
Sentinel Test for Test Isolation

Verifies that the isolated_app_client fixture correctly redirects
all file write operations to tmp_path instead of ~/Desktop/worklogs/.
"""

import pytest
from pathlib import Path
from datetime import date


class TestIsolationSentinel:
    """Verify that isolated_app_client writes to tmp_path, not real worklogs."""

    def test_post_entry_writes_to_tmp_path(self, isolated_app_client, tmp_path):
        """POST /api/entries/{date} must create files in tmp_path, not ~/Desktop/worklogs/."""
        today = date.today().isoformat()
        entry_data = {
            "date": today,
            "content": "Sentinel test content - if this appears in ~/Desktop/worklogs, isolation is broken"
        }

        response = isolated_app_client.post(f"/api/entries/{today}", json=entry_data)
        assert response.status_code == 200

        # Confirm file landed in tmp_path
        written_files = list(tmp_path.rglob("*.txt"))
        assert len(written_files) > 0, "No .txt files found in tmp_path after POST"

        # Confirm content matches
        content = written_files[0].read_text()
        assert "Sentinel test content" in content

    def test_post_entry_does_not_touch_real_worklogs(self, isolated_app_client, tmp_path):
        """POST /api/entries/{date} must NOT modify ~/Desktop/worklogs/."""
        real_base = Path("~/Desktop/worklogs").expanduser()

        # Snapshot modification times of all files in real worklogs for today's month
        today = date.today()
        month_dir = real_base / f"worklogs_{today.year}" / f"worklogs_{today.year}-{today.month:02d}"

        pre_mtimes = {}
        if month_dir.exists():
            for f in month_dir.rglob("*.txt"):
                pre_mtimes[f] = f.stat().st_mtime

        # Write via the isolated client
        today_str = today.isoformat()
        entry_data = {
            "date": today_str,
            "content": "This must NOT appear in real worklogs"
        }
        response = isolated_app_client.post(f"/api/entries/{today_str}", json=entry_data)
        assert response.status_code == 200

        # Verify no files were created or modified in real worklogs
        if month_dir.exists():
            for f in month_dir.rglob("*.txt"):
                if f in pre_mtimes:
                    assert f.stat().st_mtime == pre_mtimes[f], (
                        f"Real worklog file was modified: {f}"
                    )
                else:
                    # New file appeared in real worklogs - isolation is broken
                    assert False, f"New file created in real worklogs: {f}"

    def test_put_entry_writes_to_tmp_path(self, isolated_app_client, tmp_path):
        """PUT /api/entries/{date} must write to tmp_path, not real worklogs."""
        today = date.today().isoformat()

        # Create first
        isolated_app_client.post(
            f"/api/entries/{today}",
            json={"date": today, "content": "Initial sentinel content"}
        )

        # Update via PUT
        response = isolated_app_client.put(
            f"/api/entries/{today}",
            json={"content": "Updated sentinel content"}
        )
        assert response.status_code == 200

        # Verify updated content is in tmp_path
        written_files = list(tmp_path.rglob("*.txt"))
        assert len(written_files) > 0
        content = written_files[0].read_text()
        assert "Updated sentinel content" in content
