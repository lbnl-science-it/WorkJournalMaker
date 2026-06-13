# ABOUTME: Tests for base_path write restriction (GH#95).
# ABOUTME: Verifies that filesystem.base_path rejects paths outside allowed roots.

"""
Tests for GH#95: Unrestricted base_path setting enables arbitrary file write.

The PUT /api/settings/filesystem.base_path endpoint must reject paths
outside the user's home directory. Without this restriction, an attacker
can set base_path to any directory (e.g. /etc) and then write files via
the entry save endpoint.
"""

import pytest
from pathlib import Path


class TestBasePathWriteRestriction:
    """Verify that filesystem.base_path rejects dangerous paths on update."""

    @pytest.fixture
    def client(self, isolated_app_client):
        yield isolated_app_client

    def _update_base_path(self, client, path_value):
        """Helper: attempt to set filesystem.base_path via PUT."""
        return client.put(
            "/api/settings/filesystem.base_path",
            json={"value": path_value},
        )

    # --- Paths outside home must be rejected ---

    def test_rejects_root_path(self, client):
        """Setting base_path to / must be rejected."""
        response = self._update_base_path(client, "/")
        assert response.status_code in (400, 403, 422)

    def test_rejects_etc(self, client):
        """Setting base_path to /etc must be rejected."""
        response = self._update_base_path(client, "/etc")
        assert response.status_code in (400, 403, 422)

    def test_rejects_var_log(self, client):
        """Setting base_path to /var/log must be rejected."""
        response = self._update_base_path(client, "/var/log")
        assert response.status_code in (400, 403, 422)

    def test_rejects_tmp(self, client):
        """Setting base_path to /tmp must be rejected."""
        response = self._update_base_path(client, "/tmp")
        assert response.status_code in (400, 403, 422)

    def test_rejects_dot_dot_traversal(self, client):
        """Paths with ../ that resolve outside home must be rejected."""
        home = str(Path.home())
        traversal = home + "/../../../etc"
        response = self._update_base_path(client, traversal)
        assert response.status_code in (400, 403, 422)

    def test_rejects_relative_dot_dot_escape(self, client):
        """Relative ../ paths resolving outside home must be rejected."""
        response = self._update_base_path(client, "../../../etc")
        assert response.status_code in (400, 403, 422)

    # --- Paths inside home must be accepted ---

    def test_accepts_home_subdirectory(self, client):
        """Paths under the user's home directory should be accepted."""
        home = str(Path.home())
        safe_path = home + "/Desktop/worklogs"
        response = self._update_base_path(client, safe_path)
        assert response.status_code == 200

    def test_accepts_tilde_path(self, client):
        """Paths using ~ shorthand should be expanded and accepted."""
        response = self._update_base_path(client, "~/Desktop/worklogs")
        assert response.status_code == 200

    # --- Error message must not leak path details ---

    def test_rejection_message_is_generic(self, client):
        """Rejected paths must get a generic error, not echo the probed path."""
        response = self._update_base_path(client, "/etc/shadow")
        assert response.status_code in (400, 403, 422)
        body = response.json()
        detail = str(body.get("detail", ""))
        assert "/etc/shadow" not in detail


class TestOutputPathWriteRestriction:
    """Verify that filesystem.output_path has the same restrictions."""

    @pytest.fixture
    def client(self, isolated_app_client):
        yield isolated_app_client

    def test_rejects_etc(self, client):
        """Setting output_path to /etc must be rejected."""
        response = client.put(
            "/api/settings/filesystem.output_path",
            json={"value": "/etc"},
        )
        assert response.status_code in (400, 403, 422)

    def test_accepts_home_subdirectory(self, client):
        """Paths under home should be accepted for output_path."""
        home = str(Path.home())
        response = client.put(
            "/api/settings/filesystem.output_path",
            json={"value": home + "/Desktop/worklogs/summaries"},
        )
        assert response.status_code == 200
