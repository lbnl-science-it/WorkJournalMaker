# XSS Remediation Implementation Plan — Issue #88

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate all innerHTML-based XSS vectors by escaping dynamic data with `Utils.escapeHtml()` and sanitizing markdown output with DOMPurify.

**Architecture:** A shared `escapeHtml()` utility already exists in `web/static/js/utils.js:454`. All dynamic values interpolated into innerHTML template literals get wrapped with it. The markdown preview is the sole exception — it uses `DOMPurify.sanitize(marked.parse(content))` to preserve safe HTML while stripping malicious elements. DOMPurify loads via CDN with SRI hash.

**Tech Stack:** JavaScript (vanilla, no build step), DOMPurify 3.x via CDN, marked.js (existing), pytest + FastAPI TestClient for backend tests, Playwright for browser integration tests.

**Branch:** `fix/88-xss-innerhtml`

**Design spec:** `docs/superpowers/specs/2026-05-26-xss-remediation-design.md`

**Key discovery:** `Utils.escapeHtml()` already exists at `utils.js:454` using the DOM-based `textContent`→`innerHTML` technique. It is currently unused at any of the vulnerable sites. The implementation work is primarily wiring it into existing template literals.

**Virtual environment:** Activate `pyenv` virtual environment `WorkJournal` before running any Python tests.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `web/static/js/utils.js` | Modify | Escape `message` in `showToast()` (line 70) |
| `web/static/js/calendar.js` | Modify | Escape entry previews + content in 3 innerHTML sites |
| `web/static/js/dashboard.js` | Modify | Escape entry previews in 1 innerHTML site |
| `web/static/js/editor.js` | Modify | Wrap `marked.parse()` with `DOMPurify.sanitize()` |
| `web/static/js/settings.js` | Modify | Escape dynamic values in ~6 innerHTML sites |
| `web/static/js/summarization.js` | Modify | Escape summary data in 1 innerHTML site |
| `web/templates/entry_editor.html` | Modify | Add DOMPurify CDN with SRI; add SRI to existing marked CDN |
| `tests/test_xss_escaping.py` | Create | Unit + integration tests for escapeHtml and XSS prevention |

---

### Task 1: Add DOMPurify CDN with SRI and add SRI to marked

**Files:**
- Modify: `web/templates/entry_editor.html:201`

- [ ] **Step 1: Compute the SRI hash for marked and find DOMPurify CDN URL with SRI**

Look up the current CDN URLs and SRI hashes for:
1. `marked` — the existing URL is `https://cdn.jsdelivr.net/npm/marked/marked.min.js` (no version pin, no SRI)
2. `DOMPurify` — latest 3.x release from jsdelivr

Run:
```bash
# Get the current marked version being served and compute SRI
curl -sL "https://cdn.jsdelivr.net/npm/marked/marked.min.js" | openssl dgst -sha384 -binary | openssl base64 -A
# Get DOMPurify and compute SRI
curl -sL "https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js" | openssl dgst -sha384 -binary | openssl base64 -A
```

- [ ] **Step 2: Update entry_editor.html with SRI and DOMPurify**

In `web/templates/entry_editor.html`, replace the `extra_js` block (currently at line 200–203):

Before:
```html
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="/static/js/editor.js"></script>
{% endblock %}
```

After (use the exact hashes computed in Step 1):
```html
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/marked@<VERSION>/marked.min.js"
        integrity="sha384-<HASH>"
        crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js"
        integrity="sha384-<HASH>"
        crossorigin="anonymous"></script>
<script src="/static/js/editor.js"></script>
{% endblock %}
```

Pin `marked` to its current version so the SRI hash remains valid.

- [ ] **Step 3: Verify the page loads without console errors**

Run the web server and open the editor page:
```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && cd web && python -m uvicorn app:app --host 127.0.0.1 --port 8000 &
```
Open `http://127.0.0.1:8000/entries/2026-05-26` in a browser and check the console for SRI/loading errors.

- [ ] **Step 4: Commit**

```bash
git add web/templates/entry_editor.html
git commit -m "feat(security): add DOMPurify CDN with SRI, pin marked version with SRI for #88"
```

---

### Task 2: Sanitize markdown preview with DOMPurify

**Files:**
- Modify: `web/static/js/editor.js:230`
- Test: `tests/test_xss_escaping.py` (create)

- [ ] **Step 1: Write failing test — markdown XSS payload is stripped**

Create `tests/test_xss_escaping.py`:

```python
# ABOUTME: Tests for XSS prevention across the web frontend.
# ABOUTME: Validates that escapeHtml and DOMPurify sanitization block XSS payloads.

import pytest
from fastapi.testclient import TestClient
from web.app import app


class TestMarkdownXSSPrevention:
    """Verify that the editor page loads DOMPurify for markdown sanitization."""

    def test_editor_page_includes_dompurify(self, isolated_app_client):
        """The entry editor template must include DOMPurify before editor.js."""
        response = isolated_app_client.get("/entries/2026-01-01")
        assert response.status_code == 200
        html = response.text
        # DOMPurify must load before editor.js
        dompurify_pos = html.find("dompurify")
        editor_pos = html.find("editor.js")
        assert dompurify_pos != -1, "DOMPurify script tag not found in editor page"
        assert dompurify_pos < editor_pos, "DOMPurify must load before editor.js"

    def test_editor_page_has_sri_on_marked(self, isolated_app_client):
        """The marked script tag must have an integrity attribute."""
        response = isolated_app_client.get("/entries/2026-01-01")
        html = response.text
        # Find the marked script tag and verify it has integrity
        assert 'integrity="sha384-' in html, "marked script tag missing SRI hash"

    def test_editor_page_has_sri_on_dompurify(self, isolated_app_client):
        """The DOMPurify script tag must have an integrity attribute."""
        response = isolated_app_client.get("/entries/2026-01-01")
        html = response.text
        # Count integrity attributes — should be at least 2 (marked + DOMPurify)
        integrity_count = html.count('integrity="sha384-')
        assert integrity_count >= 2, f"Expected at least 2 SRI hashes, found {integrity_count}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py -v
```

Expected: `test_editor_page_has_sri_on_marked` FAILS (no integrity attribute on marked tag currently).

- [ ] **Step 3: Update editor.js to use DOMPurify**

In `web/static/js/editor.js`, change line 230 from:

```javascript
previewContent.innerHTML = marked.parse(this.content);
```

To:

```javascript
previewContent.innerHTML = DOMPurify.sanitize(marked.parse(this.content));
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add web/static/js/editor.js tests/test_xss_escaping.py
git commit -m "feat(security): sanitize markdown preview with DOMPurify for #88"
```

---

### Task 3: Escape dynamic data in utils.js showToast

**Files:**
- Modify: `web/static/js/utils.js:68-70`
- Test: `tests/test_xss_escaping.py` (append)

- [ ] **Step 1: Write failing test — toast message with HTML is escaped**

Append to `tests/test_xss_escaping.py`:

```python
class TestShowToastEscaping:
    """Verify that showToast escapes message content."""

    def test_toast_message_in_source_uses_escape(self):
        """The showToast method must escape its message parameter."""
        import pathlib
        utils_js = pathlib.Path("web/static/js/utils.js").read_text()
        # The toast-content div must use escapeHtml
        assert "Utils.escapeHtml(message)" in utils_js or "this.escapeHtml(message)" in utils_js, \
            "showToast must escape the message parameter with escapeHtml"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestShowToastEscaping -v
```

Expected: FAIL — `showToast` currently inserts `message` raw.

- [ ] **Step 3: Escape the message in showToast**

In `web/static/js/utils.js`, change the toast innerHTML (line 68–77). Replace:

```javascript
      <div class="toast-content">${message}</div>
```

With:

```javascript
      <div class="toast-content">${Utils.escapeHtml(message)}</div>
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestShowToastEscaping -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/static/js/utils.js tests/test_xss_escaping.py
git commit -m "fix(security): escape showToast message to prevent XSS for #88"
```

---

### Task 4: Escape dynamic data in calendar.js

**Files:**
- Modify: `web/static/js/calendar.js:155-160, 354-358`
- Test: `tests/test_xss_escaping.py` (append)

- [ ] **Step 1: Write failing test — calendar entry preview escapes HTML**

Append to `tests/test_xss_escaping.py`:

```python
class TestCalendarEscaping:
    """Verify calendar.js escapes dynamic entry data in innerHTML."""

    def test_calendar_recent_entries_uses_escape(self):
        """renderRecentEntries must escape getEntryPreview output."""
        import pathlib
        calendar_js = pathlib.Path("web/static/js/calendar.js").read_text()
        # The recent entries template must escape the preview
        assert "Utils.escapeHtml(this.getEntryPreview(" in calendar_js, \
            "renderRecentEntries must escape getEntryPreview with Utils.escapeHtml"

    def test_calendar_preview_content_uses_escape(self):
        """showEntryPreview must escape entry.content before inserting into innerHTML."""
        import pathlib
        calendar_js = pathlib.Path("web/static/js/calendar.js").read_text()
        # The preview content must escape the content before <br> replacement
        assert "Utils.escapeHtml(preview)" in calendar_js or "Utils.escapeHtml(entry.content" in calendar_js, \
            "showEntryPreview must escape content with Utils.escapeHtml"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestCalendarEscaping -v
```

Expected: FAIL — neither site uses `escapeHtml` currently.

- [ ] **Step 3: Escape dynamic data in calendar.js**

**Site 1: `renderRecentEntries` (lines 155–160)**

Replace:

```javascript
        container.innerHTML = this.recentEntries.map(entry => `
            <div class="recent-item" onclick="calendar.selectDate('${entry.date}')">
                <div class="recent-date">${Utils.formatDate(Utils.parseDate(entry.date), 'short')}</div>
                <div class="recent-preview">${this.getEntryPreview(entry)}</div>
            </div>
        `).join('');
```

With:

```javascript
        container.innerHTML = this.recentEntries.map(entry => `
            <div class="recent-item" onclick="calendar.selectDate('${Utils.escapeHtml(entry.date)}')">
                <div class="recent-date">${Utils.escapeHtml(Utils.formatDate(Utils.parseDate(entry.date), 'short'))}</div>
                <div class="recent-preview">${Utils.escapeHtml(this.getEntryPreview(entry))}</div>
            </div>
        `).join('');
```

**Site 2: `showEntryPreview` (lines 354–358)**

Replace:

```javascript
                    content.innerHTML = `
                        <div class="entry-meta">
                            <small>${entry.metadata.word_count} words • ${Utils.formatDate(Utils.parseDate(entry.modified_at || entry.created_at), 'short')}</small>
                        </div>
                        <div class="entry-text">${preview.replace(/\n/g, '<br>')}</div>
                    `;
```

With:

```javascript
                    content.innerHTML = `
                        <div class="entry-meta">
                            <small>${Utils.escapeHtml(entry.metadata.word_count)} words • ${Utils.escapeHtml(Utils.formatDate(Utils.parseDate(entry.modified_at || entry.created_at), 'short'))}</small>
                        </div>
                        <div class="entry-text">${Utils.escapeHtml(preview).replace(/\n/g, '<br>')}</div>
                    `;
```

Note: `escapeHtml(preview)` is called *before* `.replace(/\n/g, '<br>')` so that the `<br>` tags are not escaped, but any HTML in the user content is.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestCalendarEscaping -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/static/js/calendar.js tests/test_xss_escaping.py
git commit -m "fix(security): escape dynamic data in calendar.js innerHTML for #88"
```

---

### Task 5: Escape dynamic data in dashboard.js

**Files:**
- Modify: `web/static/js/dashboard.js:122-134`
- Test: `tests/test_xss_escaping.py` (append)

- [ ] **Step 1: Write failing test — dashboard entry list escapes HTML**

Append to `tests/test_xss_escaping.py`:

```python
class TestDashboardEscaping:
    """Verify dashboard.js escapes dynamic entry data in innerHTML."""

    def test_dashboard_recent_entries_uses_escape(self):
        """updateRecentEntriesSection must escape entry preview and metadata."""
        import pathlib
        dashboard_js = pathlib.Path("web/static/js/dashboard.js").read_text()
        assert "Utils.escapeHtml(this.getEntryPreview(" in dashboard_js, \
            "updateRecentEntriesSection must escape getEntryPreview with Utils.escapeHtml"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestDashboardEscaping -v
```

Expected: FAIL.

- [ ] **Step 3: Escape dynamic data in dashboard.js**

Replace lines 122–134:

```javascript
        container.innerHTML = this.recentEntries.map(entry => `
      <div class="entry-item" data-date="${entry.date}" onclick="Dashboard.openEntry('${entry.date}')">
        <div class="entry-info">
          <div class="entry-date">${Utils.formatDate(Utils.parseDate(entry.date), 'short')}</div>
          <div class="entry-preview">${this.getEntryPreview(entry)}</div>
        </div>
        <div class="entry-meta">
          <span>${entry.metadata?.word_count || 0} words</span>
          <span>•</span>
          <span>${Utils.formatDate(new Date(entry.modified_at || entry.created_at), 'short')}</span>
        </div>
      </div>
    `).join('');
```

With:

```javascript
        container.innerHTML = this.recentEntries.map(entry => `
      <div class="entry-item" data-date="${Utils.escapeHtml(entry.date)}" onclick="Dashboard.openEntry('${Utils.escapeHtml(entry.date)}')">
        <div class="entry-info">
          <div class="entry-date">${Utils.escapeHtml(Utils.formatDate(Utils.parseDate(entry.date), 'short'))}</div>
          <div class="entry-preview">${Utils.escapeHtml(this.getEntryPreview(entry))}</div>
        </div>
        <div class="entry-meta">
          <span>${Utils.escapeHtml(entry.metadata?.word_count || 0)} words</span>
          <span>•</span>
          <span>${Utils.escapeHtml(Utils.formatDate(new Date(entry.modified_at || entry.created_at), 'short'))}</span>
        </div>
      </div>
    `).join('');
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestDashboardEscaping -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/static/js/dashboard.js tests/test_xss_escaping.py
git commit -m "fix(security): escape dynamic data in dashboard.js innerHTML for #88"
```

---

### Task 6: Escape dynamic data in settings.js

**Files:**
- Modify: `web/static/js/settings.js:162-207, 857-871, 1726-1750`
- Test: `tests/test_xss_escaping.py` (append)

- [ ] **Step 1: Write failing test — settings templates escape dynamic values**

Append to `tests/test_xss_escaping.py`:

```python
class TestSettingsEscaping:
    """Verify settings.js escapes dynamic data in innerHTML."""

    def test_settings_description_uses_escape(self):
        """renderSettingItem must escape setting.description."""
        import pathlib
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        # The setting description must be escaped
        assert "Utils.escapeHtml(setting.description" in settings_js, \
            "renderSettingItem must escape setting.description with Utils.escapeHtml"

    def test_settings_sync_error_uses_escape(self):
        """renderSyncHistory must escape record.error_message."""
        import pathlib
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        assert "Utils.escapeHtml(record.error_message" in settings_js, \
            "renderSyncHistory must escape record.error_message with Utils.escapeHtml"

    def test_settings_validation_error_uses_escape(self):
        """updateWorkWeekValidationDisplay must escape error.message."""
        import pathlib
        settings_js = pathlib.Path("web/static/js/settings.js").read_text()
        assert "Utils.escapeHtml(error.message" in settings_js, \
            "updateWorkWeekValidationDisplay must escape error.message with Utils.escapeHtml"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestSettingsEscaping -v
```

Expected: FAIL — no escaping currently.

- [ ] **Step 3: Escape dynamic data in settings.js**

**Site 1: `renderSettingItem` (lines 177–207)**

In the template literal, escape `setting.description`, `setting.key`, and `formatSettingLabel()`:

Replace:
```javascript
            <h3 class="setting-label">${this.formatSettingLabel(setting.key)}</h3>
            <p class="setting-description">${setting.description || ''}</p>
```

With:
```javascript
            <h3 class="setting-label">${Utils.escapeHtml(this.formatSettingLabel(setting.key))}</h3>
            <p class="setting-description">${Utils.escapeHtml(setting.description || '')}</p>
```

Also escape `setting.key` in `data-key` attributes throughout the template:

Replace every `data-key="${setting.key}"` with `data-key="${Utils.escapeHtml(setting.key)}"` within `renderSettingItem`.

**Site 2: `updateWorkWeekValidationDisplay` (lines 857–871)**

Replace:
```javascript
                        `<div class="validation-error">
                            <span class="error-message">${error.message}</span>
                            ${error.suggestion ? `<span class="error-suggestion">${error.suggestion}</span>` : ''}
                        </div>`
```

With:
```javascript
                        `<div class="validation-error">
                            <span class="error-message">${Utils.escapeHtml(error.message)}</span>
                            ${error.suggestion ? `<span class="error-suggestion">${Utils.escapeHtml(error.suggestion)}</span>` : ''}
                        </div>`
```

**Site 3: `renderSyncHistory` (lines 1726–1750)**

Replace:
```javascript
                        <div class="history-type">${this.formatSyncType(record.sync_type)}</div>
                        <div class="history-details">
                            ${record.entries_processed || 0} processed, 
                            ${record.entries_added || 0} added, 
                            ${record.entries_updated || 0} updated
                            ${record.error_message ? ` - ${record.error_message}` : ''}
                        </div>
```

With:
```javascript
                        <div class="history-type">${Utils.escapeHtml(this.formatSyncType(record.sync_type))}</div>
                        <div class="history-details">
                            ${Utils.escapeHtml(record.entries_processed || 0)} processed, 
                            ${Utils.escapeHtml(record.entries_added || 0)} added, 
                            ${Utils.escapeHtml(record.entries_updated || 0)} updated
                            ${record.error_message ? ` - ${Utils.escapeHtml(record.error_message)}` : ''}
                        </div>
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestSettingsEscaping -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/static/js/settings.js tests/test_xss_escaping.py
git commit -m "fix(security): escape dynamic data in settings.js innerHTML for #88"
```

---

### Task 7: Escape dynamic data in summarization.js

**Files:**
- Modify: `web/static/js/summarization.js:507-530`
- Test: `tests/test_xss_escaping.py` (append)

- [ ] **Step 1: Write failing test — summarization history escapes HTML**

Append to `tests/test_xss_escaping.py`:

```python
class TestSummarizationEscaping:
    """Verify summarization.js escapes dynamic summary data in innerHTML."""

    def test_summarization_history_uses_escape(self):
        """renderHistory must escape summary data."""
        import pathlib
        summarization_js = pathlib.Path("web/static/js/summarization.js").read_text()
        assert "Utils.escapeHtml(summary.summary_type)" in summarization_js, \
            "renderHistory must escape summary.summary_type with Utils.escapeHtml"

    def test_summarization_preview_uses_escape(self):
        """renderHistory must escape getHistoryPreview output."""
        import pathlib
        summarization_js = pathlib.Path("web/static/js/summarization.js").read_text()
        assert "Utils.escapeHtml(this.getHistoryPreview(" in summarization_js, \
            "renderHistory must escape getHistoryPreview with Utils.escapeHtml"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestSummarizationEscaping -v
```

Expected: FAIL.

- [ ] **Step 3: Escape dynamic data in summarization.js**

Replace lines 507–530:

```javascript
        container.innerHTML = this.summaryHistory.map(summary => `
      <div class="history-item">
        <div class="history-header">
          <h3 class="history-title">${summary.summary_type} Summary</h3>
          <span class="history-status ${summary.status}">${summary.status}</span>
        </div>
        <div class="history-meta">
          ${summary.start_date} to ${summary.end_date} • ${new Date(summary.created_at).toLocaleDateString()}
        </div>
        <div class="history-preview">
          ${this.getHistoryPreview(summary)}
        </div>
        <div class="history-actions">
          <button class="btn btn-secondary btn-sm" onclick="summarizationInterface.viewHistoryItem('${summary.task_id}')">
            View
          </button>
          ${summary.status === 'completed' ? `
            <button class="btn btn-secondary btn-sm" onclick="summarizationInterface.downloadHistoryItem('${summary.task_id}')">
              Download
            </button>
          ` : ''}
        </div>
      </div>
    `).join('');
```

With:

```javascript
        container.innerHTML = this.summaryHistory.map(summary => `
      <div class="history-item">
        <div class="history-header">
          <h3 class="history-title">${Utils.escapeHtml(summary.summary_type)} Summary</h3>
          <span class="history-status ${Utils.escapeHtml(summary.status)}">${Utils.escapeHtml(summary.status)}</span>
        </div>
        <div class="history-meta">
          ${Utils.escapeHtml(summary.start_date)} to ${Utils.escapeHtml(summary.end_date)} • ${Utils.escapeHtml(new Date(summary.created_at).toLocaleDateString())}
        </div>
        <div class="history-preview">
          ${Utils.escapeHtml(this.getHistoryPreview(summary))}
        </div>
        <div class="history-actions">
          <button class="btn btn-secondary btn-sm" onclick="summarizationInterface.viewHistoryItem('${Utils.escapeHtml(summary.task_id)}')">
            View
          </button>
          ${summary.status === 'completed' ? `
            <button class="btn btn-secondary btn-sm" onclick="summarizationInterface.downloadHistoryItem('${Utils.escapeHtml(summary.task_id)}')">
              Download
            </button>
          ` : ''}
        </div>
      </div>
    `).join('');
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestSummarizationEscaping -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/static/js/summarization.js tests/test_xss_escaping.py
git commit -m "fix(security): escape dynamic data in summarization.js innerHTML for #88"
```

---

### Task 8: Integration test — XSS payload in journal entry is neutralized

**Files:**
- Test: `tests/test_xss_escaping.py` (append)

- [ ] **Step 1: Write integration test — entry with XSS payload returns escaped HTML**

Append to `tests/test_xss_escaping.py`:

```python
class TestXSSIntegration:
    """End-to-end tests verifying XSS payloads are neutralized in API responses."""

    XSS_PAYLOADS = [
        '<script>alert("xss")</script>',
        '<img src=x onerror=alert(1)>',
        '<svg onload=alert(1)>',
        '"><script>alert(1)</script>',
        "' onmouseover='alert(1)'",
    ]

    def test_entry_content_api_returns_raw_content(self, isolated_app_client):
        """API returns raw content (escaping is the frontend's job)."""
        # Create an entry with XSS payload
        payload = '<script>alert("xss")</script>Normal text'
        response = isolated_app_client.put(
            "/api/entries/2026-01-15",
            json={"content": payload}
        )
        assert response.status_code in (200, 201)

        # Fetch it back — API should return raw content
        response = isolated_app_client.get("/api/entries/2026-01-15?include_content=true")
        assert response.status_code == 200
        data = response.json()
        assert '<script>' in data['content'], \
            "API should return raw content; escaping is the frontend's responsibility"

    def test_dashboard_page_does_not_contain_raw_script_tag(self, isolated_app_client):
        """Dashboard HTML response must not contain unescaped script from entry content."""
        # Create entry with XSS
        isolated_app_client.put(
            "/api/entries/2026-01-15",
            json={"content": '<script>alert("xss")</script>'}
        )
        # Dashboard is server-rendered — verify no raw script tag in HTML
        response = isolated_app_client.get("/")
        assert response.status_code == 200
        # The dashboard template itself shouldn't inline entry content
        # (it's loaded via JS), so this is a sanity check
        assert '<script>alert("xss")</script>' not in response.text
```

- [ ] **Step 2: Run integration tests**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py::TestXSSIntegration -v
```

Expected: PASS — API returns raw content (by design), dashboard doesn't inline it.

- [ ] **Step 3: Commit**

```bash
git add tests/test_xss_escaping.py
git commit -m "test(security): add XSS integration tests for #88"
```

---

### Task 9: Full audit — grep for remaining unescaped innerHTML

**Files:**
- No new files — audit only

- [ ] **Step 1: Run audit grep across all JS files**

```bash
grep -n 'innerHTML' web/static/js/*.js | grep -v 'escapeHtml\|DOMPurify\|sanitize' | grep '\${'
```

This finds innerHTML assignments that interpolate dynamic values (`${`) but don't use `escapeHtml` or `DOMPurify`. Each line in the output needs manual review — it's either:
1. A missed site that needs escaping (fix it)
2. A site that only interpolates safe structural HTML (document why it's safe)

- [ ] **Step 2: Fix any missed sites found in the audit**

Apply `Utils.escapeHtml()` to any remaining dynamic data found. Add corresponding tests.

- [ ] **Step 3: Run full test suite**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_xss_escaping.py -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit any remaining fixes**

```bash
git add -A
git commit -m "fix(security): escape remaining innerHTML sites found by audit for #88"
```

---

### Task 10: Update todo.md and verify

**Files:**
- Modify: `todo.md`

- [ ] **Step 1: Mark #88 as complete in todo.md**

Change `- [ ] [#88]` to `- [x] [#88]` in the Cluster S section of `todo.md`.

- [ ] **Step 2: Run the complete test suite to verify no regressions**

```bash
cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/ -v --timeout=60
```

Expected: All tests pass, including the new XSS tests.

- [ ] **Step 3: Commit**

```bash
git add todo.md
git commit -m "chore: mark #88 XSS remediation complete in todo.md"
```
