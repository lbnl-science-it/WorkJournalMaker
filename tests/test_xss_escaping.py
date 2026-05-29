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


class TestShowToastEscaping:
    """Verify that showToast escapes message content."""

    def test_toast_message_uses_escape(self):
        """The showToast method must escape its message parameter."""
        utils_js = pathlib.Path("web/static/js/utils.js").read_text()
        assert "Utils.escapeHtml(message)" in utils_js, \
            "showToast must escape the message parameter with escapeHtml"


class TestCalendarEscaping:
    """Verify calendar.js escapes dynamic entry data in innerHTML."""

    def test_calendar_recent_entries_uses_escape(self):
        """renderRecentEntries must escape getEntryPreview output."""
        calendar_js = pathlib.Path("web/static/js/calendar.js").read_text()
        assert "Utils.escapeHtml(this.getEntryPreview(" in calendar_js, \
            "renderRecentEntries must escape getEntryPreview with Utils.escapeHtml"

    def test_calendar_preview_content_uses_escape(self):
        """showEntryPreview must escape entry.content before inserting into innerHTML."""
        calendar_js = pathlib.Path("web/static/js/calendar.js").read_text()
        assert "Utils.escapeHtml(preview)" in calendar_js, \
            "showEntryPreview must escape content with Utils.escapeHtml"


class TestDashboardEscaping:
    """Verify dashboard.js escapes dynamic entry data in innerHTML."""

    def test_dashboard_recent_entries_uses_escape(self):
        """updateRecentEntriesSection must escape entry preview and metadata."""
        dashboard_js = pathlib.Path("web/static/js/dashboard.js").read_text()
        assert "Utils.escapeHtml(this.getEntryPreview(" in dashboard_js, \
            "updateRecentEntriesSection must escape getEntryPreview with Utils.escapeHtml"


class TestSettingsEscaping:
    """Verify settings.js escapes dynamic data in innerHTML."""

    def test_settings_description_uses_escape(self):
        """renderSettingItem must escape setting.description."""
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        assert "Utils.escapeHtml(setting.description" in settings_js, \
            "renderSettingItem must escape setting.description with Utils.escapeHtml"

    def test_settings_sync_error_uses_escape(self):
        """renderSyncHistory must escape record.error_message."""
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        assert "Utils.escapeHtml(record.error_message" in settings_js, \
            "renderSyncHistory must escape record.error_message with Utils.escapeHtml"

    def test_settings_validation_error_uses_escape(self):
        """updateWorkWeekValidationDisplay must escape error.message."""
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        assert "Utils.escapeHtml(error.message" in settings_js, \
            "updateWorkWeekValidationDisplay must escape error.message with Utils.escapeHtml"

    def test_settings_sync_status_uses_escape(self):
        """renderSyncStatus must escape dbStats and syncStatus values."""
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        assert "Utils.escapeHtml(String(dbStats.total_entries" in settings_js, \
            "renderSyncStatus must escape dbStats.total_entries with Utils.escapeHtml"
        assert "Utils.escapeHtml(new Date(syncStatus.last_sync).toLocaleString())" in settings_js, \
            "renderSyncStatus must escape last_sync date with Utils.escapeHtml"
        assert "Utils.escapeHtml(this.formatFileSize(" in settings_js, \
            "renderSyncStatus must escape formatFileSize output with Utils.escapeHtml"

    def test_settings_data_key_attributes_use_escape(self):
        """renderSettingItem must escape setting.key in data-key attributes."""
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        assert 'data-key="${Utils.escapeHtml(setting.key)}"' in settings_js, \
            "renderSettingItem must escape setting.key in data-key attributes"


class TestSummarizationEscaping:
    """Verify summarization.js escapes dynamic summary data in innerHTML."""

    def test_summarization_history_uses_escape(self):
        """renderHistory must escape summary data."""
        summarization_js = pathlib.Path("web/static/js/summarization.js").read_text()
        assert "Utils.escapeHtml(summary.summary_type)" in summarization_js, \
            "renderHistory must escape summary.summary_type with Utils.escapeHtml"

    def test_summarization_preview_uses_escape(self):
        """renderHistory must escape getHistoryPreview output."""
        summarization_js = pathlib.Path("web/static/js/summarization.js").read_text()
        assert "Utils.escapeHtml(this.getHistoryPreview(" in summarization_js, \
            "renderHistory must escape getHistoryPreview with Utils.escapeHtml"


class TestXSSIntegration:
    """End-to-end tests verifying XSS payloads are neutralized in API responses."""

    def test_entry_content_api_returns_raw_content(self, isolated_app_client):
        """API returns raw content (escaping is the frontend's job)."""
        payload = '<script>alert("xss")</script>Normal text'
        response = isolated_app_client.post(
            "/api/entries/2025-01-15",
            json={"date": "2025-01-15", "content": payload}
        )
        assert response.status_code in (200, 201), f"Create failed: {response.text}"

        response = isolated_app_client.get("/api/entries/2025-01-15?include_content=true")
        assert response.status_code == 200
        data = response.json()
        assert '<script>' in data['content'], \
            "API should return raw content; escaping is the frontend's responsibility"

    def test_dashboard_page_does_not_render_entry_content_server_side(self, isolated_app_client):
        """Dashboard loads entries via JS, so the template must never inline entry content."""
        isolated_app_client.post(
            "/api/entries/2025-01-15",
            json={"date": "2025-01-15", "content": '<img src=x onerror=alert(1)>'}
        )
        response = isolated_app_client.get("/")
        assert response.status_code == 200
        assert 'onerror=alert(1)' not in response.text, \
            "Dashboard template must not inline entry content server-side"
