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

    @pytest.mark.skipif(
        not (Path("~/Desktop/worklogs").expanduser() / f"worklogs_{date.today().year}"
             / f"worklogs_{date.today().year}-{date.today().month:02d}").exists(),
        reason="Real worklogs month directory does not exist — test cannot verify isolation"
    )
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

    def test_delete_entry_without_prior_read_or_write(self, isolated_app_client, tmp_path):
        """delete_entry must initialize file_discovery even without a prior GET/POST.

        Exercises the P1 bug: delete_entry skips _ensure_file_discovery_initialized(),
        so calling it when file_discovery is None causes _construct_file_path_async
        to raise AttributeError. We test at the service level because the API
        endpoint's get_entry_by_date pre-check masks the bug.
        """
        import asyncio
        from web.app import app as web_app

        em = web_app.state.entry_manager

        # Simulate the uninitialized state that exists before any GET/POST
        saved_fd = em.file_discovery
        saved_bp = em._current_base_path
        em.file_discovery = None
        em._current_base_path = None

        try:
            today = date.today()
            # Call delete_entry directly — with proper initialization, deleting
            # a non-existent entry succeeds (True). Without initialization, the
            # catch-all silently swallows the AttributeError and returns False.
            result = asyncio.get_event_loop().run_until_complete(em.delete_entry(today))
            assert result is True, (
                "delete_entry returned False — likely failed due to uninitialized "
                "file_discovery (AttributeError swallowed by catch-all)"
            )
        finally:
            em.file_discovery = saved_fd
            em._current_base_path = saved_bp

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
