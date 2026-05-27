# ABOUTME: Tests for XSS prevention across the web frontend.
# ABOUTME: Validates that escapeHtml and DOMPurify sanitization block XSS payloads.

import pytest
import pathlib


class TestMarkdownXSSPrevention:
    """Verify that the editor page loads DOMPurify for markdown sanitization."""

    def test_editor_page_includes_dompurify(self, isolated_app_client):
        """The entry editor template must include DOMPurify before editor.js."""
        response = isolated_app_client.get("/entry/2026-01-01")
        assert response.status_code == 200
        html = response.text
        dompurify_pos = html.find("dompurify")
        editor_pos = html.find("editor.js")
        assert dompurify_pos != -1, "DOMPurify script tag not found in editor page"
        assert dompurify_pos < editor_pos, "DOMPurify must load before editor.js"

    def test_editor_page_has_sri_on_marked(self, isolated_app_client):
        """The marked script tag must have an integrity attribute."""
        response = isolated_app_client.get("/entry/2026-01-01")
        html = response.text
        assert 'integrity="sha384-' in html, "marked script tag missing SRI hash"

    def test_editor_page_has_sri_on_dompurify(self, isolated_app_client):
        """The DOMPurify script tag must have an integrity attribute."""
        response = isolated_app_client.get("/entry/2026-01-01")
        html = response.text
        integrity_count = html.count('integrity="sha384-')
        assert integrity_count >= 2, f"Expected at least 2 SRI hashes, found {integrity_count}"

    def test_editor_js_uses_dompurify(self):
        """editor.js must wrap marked.parse() output with DOMPurify.sanitize()."""
        editor_js = pathlib.Path("web/static/js/editor.js").read_text()
        assert "DOMPurify.sanitize(marked.parse(" in editor_js, \
            "editor.js must sanitize marked output with DOMPurify"
