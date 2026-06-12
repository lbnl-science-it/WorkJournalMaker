# ABOUTME: Tests that all template-based routes render without server errors.
# ABOUTME: Catches Jinja2/Starlette API incompatibilities in TemplateResponse calls.

import pytest


class TestTemplateRoutes:
    """Verify that every template route returns HTTP 200, not 500."""

    def test_dashboard_renders(self, isolated_app_client):
        response = isolated_app_client.get("/")
        assert response.status_code == 200, f"Dashboard failed: {response.text[:200]}"

    def test_entry_editor_renders(self, isolated_app_client):
        response = isolated_app_client.get("/entry/2026-01-01")
        assert response.status_code == 200, f"Entry editor failed: {response.text[:200]}"

    def test_calendar_renders(self, isolated_app_client):
        response = isolated_app_client.get("/calendar")
        assert response.status_code == 200, f"Calendar failed: {response.text[:200]}"

    def test_summarization_renders(self, isolated_app_client):
        response = isolated_app_client.get("/summarize")
        assert response.status_code == 200, f"Summarization failed: {response.text[:200]}"

    def test_settings_renders(self, isolated_app_client):
        response = isolated_app_client.get("/settings")
        assert response.status_code == 200, f"Settings failed: {response.text[:200]}"
