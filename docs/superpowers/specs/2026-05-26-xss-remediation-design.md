# XSS Remediation Design — Issue #88

## Problem

Journal entry content (user-controlled text) is inserted via `innerHTML` without escaping in multiple frontend files. A journal entry containing `<img src=x onerror=alert(document.cookie)>` executes immediately when viewed. Server-sourced data (settings descriptions, error messages, summary results) is also inserted raw.

## Approach

**Shared `escapeHtml()` utility + DOMPurify for markdown** (Approach A from brainstorming).

All dynamic values interpolated into innerHTML template literals are wrapped with `Utils.escapeHtml()`. The markdown preview is the exception — it uses `DOMPurify.sanitize(marked.parse(content))` to preserve legitimate HTML rendering while stripping malicious elements.

## Components

### 1. `Utils.escapeHtml()` — `web/static/js/utils.js`

Static method on the existing `Utils` class. Escapes `& < > " '` — the five characters that enable HTML injection. Returns empty string for null/undefined.

### 2. DOMPurify — CDN with SRI hash

Loaded in `web/templates/entry_editor.html` via jsdelivr CDN with a Subresource Integrity hash. Default DOMPurify config strips `<script>`, event handlers (`onerror`, `onclick`), `javascript:` URIs, but preserves safe HTML elements that markdown produces (`<p>`, `<h1>`, `<code>`, `<a>`, `<em>`, etc.).

### 3. SRI hash on existing `marked` CDN tag

While editing `entry_editor.html` to add DOMPurify, we also add the SRI hash to the existing `marked` script tag. Partial coverage for issue #92.

## Remediation Site Map

### calendar.js — 3 sites need escapeHtml

- **Lines 155–160**: `getEntryPreview(entry)` and `entry.date` in onclick
- **Lines 354–358**: `entry.content` preview — escape content before `<br>` replace; escape `word_count` and date metadata
- Lines 131, 136, 147, 165, 336, 361, 364, 370: Safe (static HTML, no dynamic data)

### dashboard.js — 1 site

- **Lines 122–134**: `getEntryPreview(entry)`, `entry.date`, `word_count`, timestamps

### editor.js — 1 site

- **Line 230**: `marked.parse()` output → `DOMPurify.sanitize(marked.parse(content))`

### settings.js — ~6 sites

- **Lines 162–207**: `setting.description`, `setting.key`, `formatSettingLabel()`
- **Lines 365, 373, 381**: Path validation messages with user-provided paths
- **Lines 857, 880**: Validation container with path values
- **Line 984**: Preview HTML — review `previewHtml` source
- **Lines 1726–1750**: Sync history — `record.error_message`, `record.sync_type`

### summarization.js — 1 site

- **Lines 507–530**: `summary.summary_type`, dates, `task_id`, `getHistoryPreview()`

### utils.js — 1 site

- **Lines 68–70**: `showToast()` — escape `message` parameter

## Testing

### Unit tests for `escapeHtml()`

- Escapes all five characters correctly
- Handles null, undefined, empty string
- Handles non-string inputs (numbers, booleans coerced via `String()`)
- Passes through already-safe strings unchanged

### Integration tests (Playwright)

- Create journal entries containing XSS payloads via test API
- Verify rendered HTML contains escaped entities, not executable tags
- All tests use isolated test databases — no production data touched

### Regression tests

- Normal journal content (plain text) renders correctly
- Markdown preview still produces styled HTML (headings, bold, code blocks)
- Malicious elements stripped from markdown preview (script tags, onerror)

## Scope

### In scope

- `Utils.escapeHtml()` utility
- DOMPurify via CDN with SRI in `entry_editor.html`
- SRI hash on existing `marked` CDN tag (partial #92)
- Escape all dynamic data in innerHTML template literals (~15–18 sites)
- Sanitize `marked.parse()` output with DOMPurify
- Tests

### Out of scope

- SRI on CDN tags in other templates (#92 full scope)
- Inline onclick attribute escaping (#93)
- CSP headers (#91)
- Refactoring template literal patterns
