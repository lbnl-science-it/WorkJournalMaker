# ABOUTME: Tests for path traversal protection on the validate-path endpoint.
# ABOUTME: Verifies that filesystem probing is restricted to allowed directories.

"""
Tests for GH#90: Path traversal via filesystem validate-path endpoint.

The /api/settings/filesystem/validate-path endpoint must restrict path
validation and directory creation to allowed roots (user home directory).
Paths outside the allowed roots must be rejected with HTTP 403.
"""

import pytest
from pathlib import Path


class TestPathTraversalProtection:
    """Verify the validate-path endpoint blocks path traversal attacks."""

    @pytest.fixture
    def client(self, isolated_app_client):
        yield isolated_app_client

    # --- Paths outside allowed roots must be rejected ---

    def test_rejects_etc_passwd_probe(self, client):
        """Probing /etc/passwd must be blocked."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "/etc/passwd"}
        )
        assert response.status_code == 403

    def test_rejects_root_path(self, client):
        """Probing / must be blocked."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "/"}
        )
        assert response.status_code == 403

    def test_rejects_var_log_probe(self, client):
        """Probing /var/log must be blocked."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "/var/log"}
        )
        assert response.status_code == 403

    def test_rejects_dot_dot_traversal(self, client):
        """Paths using ../ to escape the home directory must be blocked."""
        home = str(Path.home())
        # Attempt to traverse out of home via ../
        traversal_path = home + "/../../../etc/passwd"
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": traversal_path}
        )
        assert response.status_code == 403

    def test_rejects_relative_dot_dot_traversal(self, client):
        """Relative paths with ../ that resolve outside home must be blocked."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "../../../etc/passwd"}
        )
        assert response.status_code == 403

    def test_rejects_create_outside_allowed_root(self, client):
        """Creating directories outside allowed roots must be blocked."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "/tmp/evil_directory", "create_if_missing": True}
        )
        assert response.status_code == 403

    # --- Paths inside allowed roots must be permitted ---

    def test_allows_home_subdirectory(self, client):
        """Paths under the user's home directory are allowed."""
        home = str(Path.home())
        safe_path = home + "/Desktop/worklogs"
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": safe_path}
        )
        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert "exists" in data

    def test_allows_home_with_tilde(self, client):
        """Paths using ~ shorthand should be expanded and allowed."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "~/Desktop/worklogs"}
        )
        assert response.status_code == 200

    def test_allows_create_inside_home(self, client, tmp_path):
        """Creating directories inside the home dir should work."""
        # Use a path under home that we can safely create
        home = str(Path.home())
        test_path = home + "/test_wjm_validate_path_creation"
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": test_path, "create_if_missing": True}
        )
        # Clean up if created
        created = Path(test_path)
        if created.exists():
            created.rmdir()
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["is_directory"] is True

    # --- Response must not leak sensitive path info ---

    def test_response_excludes_absolute_path_field(self, client):
        """The response must not include a separate absolute_path field."""
        home = str(Path.home())
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": home}
        )
        assert response.status_code == 200
        data = response.json()
        # absolute_path is redundant info leakage; only 'path' should be present
        assert "absolute_path" not in data

    # --- Error message must not reveal filesystem details ---

    def test_rejection_message_is_generic(self, client):
        """Rejected paths must get a generic error, not reveal path details."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "/etc/shadow"}
        )
        assert response.status_code == 403
        data = response.json()
        # Should not echo back the probed path
        assert "/etc/shadow" not in data.get("detail", "")
