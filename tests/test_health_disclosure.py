# ABOUTME: Security tests for the public health endpoint.
# ABOUTME: Verifies no filesystem paths, DB paths, or provider details leak in responses.
"""Tests that GET /api/health/ does not disclose internal details."""

import json
import pytest


class TestHealthPublicEndpointDisclosure:
    """The public health endpoint must not expose internal infrastructure details."""

    def test_no_base_path_in_response(self, isolated_app_client):
        """Filesystem base_path must not appear anywhere in the health response."""
        response = isolated_app_client.get("/api/health/")
        body = json.dumps(response.json())
        assert "base_path" not in body

    def test_no_database_path_in_response(self, isolated_app_client):
        """Database path must not appear anywhere in the health response."""
        response = isolated_app_client.get("/api/health/")
        body = json.dumps(response.json())
        assert "database_path" not in body

    def test_no_llm_provider_in_response(self, isolated_app_client):
        """LLM provider name must not appear in the health response."""
        response = isolated_app_client.get("/api/health/")
        body = json.dumps(response.json())
        assert "llm_provider" not in body

    def test_required_fields_present(self, isolated_app_client):
        """The health response must still contain its contractual top-level fields."""
        response = isolated_app_client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        for field in ["status", "service", "version", "timestamp"]:
            assert field in data, f"Missing required field: {field}"

    def test_components_contain_only_status(self, isolated_app_client):
        """Each component in the health response should expose only a status field."""
        response = isolated_app_client.get("/api/health/")
        data = response.json()
        components = data.get("components", {})
        for name, component in components.items():
            assert list(component.keys()) == ["status"], (
                f"Component '{name}' exposes keys beyond 'status': {list(component.keys())}"
            )
