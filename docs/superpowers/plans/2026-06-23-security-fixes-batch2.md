# Security Fixes Implementation Plan

## Progress

- [x] Phase 1 — Verify #8 (showToast XSS already fixed)
- [x] Phase 2 — #12 (debug log), #7 (test pages), #38 (cache-busting) — branch: `security/quick-fixes-7-12`
- [x] Phase 3 — #5, #6, #10, #14 (server-side validation) — branch: `security/validation-cluster-5-6-10-14`
- [x] **SMOKE TEST CHECKPOINT 1** — pause here for live testing
- [x] Phase 4 — #11, #13 (information disclosure) — branch: `security/info-disclosure-11-13`
- [x] Phase 5 — #9 (WebSocket auth) — branch: `security/issue-9-websocket-auth`
- [x] **SMOKE TEST CHECKPOINT 2** — pause here for live testing
- [ ] Phase 6a — #33/#36 (LLM system/user separation)
- [ ] Phase 6b — #34/#37 (LLM output schema validation)

## Context

The Work Journal Maker web application has 12 remaining open security issues (chainlink #5-#14, #33/#36, #34/#37). The first wave of high-severity fixes (path traversal, XSS framework, CSRF, CORS, CSP headers, etc.) was completed in earlier sessions. This plan addresses the remaining medium-severity issues in a dependency-aware order that minimizes file re-visits and merge conflicts.

Key finding during exploration: **Issue #8 is already fixed** (`Utils.escapeHtml()` applied in `showToast`). Issues #33/#36 and #34/#37 are duplicate pairs.

---

## Phase 1 — Verify & Close (Issue #8)

**Action:** Run existing test `tests/test_xss_escaping.py`, confirm passing, close issue #8.
**No code changes needed.**

---

## Phase 2 — Quick Independent Fixes (#7, #12)

**Branch:** `security/quick-fixes-7-12`

### Issue #12 — Debug log leaks request body
- **File:** `bedrock_client.py:211`
- **Fix:** Replace `json.dumps(request_body)` with structure-only log (key names + message count)
- **Tests:** `tests/test_bedrock_debug_log.py` — assert debug output contains no prompt text

### Issue #7 — Test/debug pages in production
- **File:** `web/app.py` (conditional `/test` route registration)
- **File:** Delete `web/static/test_date_parsing_fix.html`
- **Fix:** Add `WORK_JOURNAL_DEBUG` env var check; gate `/test` route behind it
- **Tests:** `tests/test_test_route_gating.py` — 404 without env var, static test file gone

---

## Phase 3 — Server-Side Validation Cluster (#5, #6, #10, #14)

**Branch:** `security/validation-cluster-5-6-10-14`

### Issue #5 — Scheduler config DoS
- **File:** `web/api/sync.py:288-319`
- **Fix:** Create `SchedulerConfigRequest` Pydantic model with `Field(ge=1, le=86400)` for `incremental_seconds`, `Field(ge=1, le=168)` for `full_hours`
- **Pattern:** Matches existing `IncrementalSyncRequest` in same file
- **Tests:** `tests/test_scheduler_config_validation.py` — zero, negative, too-large values → 422

### Issue #6 — Entry content unbounded
- **File:** `web/api/entries.py:255-276`
- **Fix:** Create `UpdateContentRequest` model with `Field(max_length=500_000)`
- **Tests:** `tests/test_entry_content_validation.py` — oversized → 422, normal → accepted

### Issue #10 — Timezone accepts arbitrary strings
- **Files:** `web/services/work_week_service.py:836-847`, `web/services/settings_service.py:1326-1328`
- **Fix:** Validate against `zoneinfo.ZoneInfo()`; promote timezone failure from warning to error
- **Tests:** `tests/test_work_week_timezone_validation.py` — valid IANA tz passes, bogus rejected

### Issue #14 — Client-only validation gaps (remaining)
- `since_days` already fixed with `Field(ge=1, le=365)` ✓
- **File:** `web/models/journal.py` — Add 365-day max range check to `SummaryRequest.validate_date_range`
- **File:** `web/models/settings.py` — Add `start_day != end_day` model validator to `WorkWeekConfigRequest`
- **Tests:** `tests/test_summarization_date_validation.py`, `tests/test_work_week_day_validation.py`

---

## Phase 4 — Information Disclosure (#11, #13)

**Branch:** `security/info-disclosure-11-13`

### Issue #11 — raw_response stores full exception strings
- **File:** `base_llm_client.py:146-162`
- **Fix:** Change `raw_response=f"ERROR ({error_type}): {str(e)}"` → `raw_response=f"ERROR ({error_type})"`
- **Update:** Existing test assertion in `tests/test_base_llm_client.py`
- **Tests:** Assert raw_response contains no exception message content (ARNs, URIs, etc.)

### Issue #13 — file_path exposed in API responses
- **Files:** `web/models/journal.py` (remove `file_path` from `JournalEntryResponse`), `web/services/entry_manager.py` (remove kwarg), `web/services/calendar_service.py` (remove from dict)
- **Tests:** `tests/test_file_path_disclosure.py` — GET endpoints return no `file_path` key

---

## Phase 5 — WebSocket Auth (#9)

**Branch:** `security/issue-9-websocket-auth`

- **File:** `web/api/summarization.py:461-547`
- **Fix:** Add auth gate to both WS endpoints mirroring `app.py:279-292` pattern (check `auth_config.enabled`, validate `?token=` query param via `decode_access_token`)
- **Note:** General `/ws` in `app.py` already has auth gating — only summarization WS endpoints lack it
- **Tests:** `tests/test_summarization_ws_auth.py` — reject without token (4001), accept with valid token, bypass when auth disabled

---

## Phase 6 — LLM Pipeline Security (#33/#36, #34/#37)

### 6a: Issue #33/#36 — Separate system/user messages

**Branch:** `security/issue-33-system-user-separation`

- **Files:** `base_llm_client.py`, `bedrock_client.py`, `google_genai_client.py`, `cborg_client.py`
- **Fix:**
  - Split `ANALYSIS_PROMPT` into `SYSTEM_PROMPT` + `USER_PROMPT_TEMPLATE`
  - Change `_create_analysis_prompt()` → returns `Tuple[str, str]`
  - Change `_make_api_call(prompt)` → `_make_api_call(system, user)`
  - Bedrock: add top-level `"system"` key in request body
  - Google GenAI: use `system_instruction` in config
  - CBORG: add `{"role": "system", ...}` message
- **Tests:** `tests/test_llm_system_user_separation.py` — verify each provider sends system/user in separate API fields
- **Close:** #33 as duplicate of #36 (or vice versa)

### 6b: Issue #34/#37 — Validate LLM output schema

**Branch:** `security/issue-34-llm-output-validation`

- **Files:** `base_llm_client.py` (`_parse_response`), `summary_generator.py` (`_generate_period_summary`)
- **Fix:**
  - Add element-level validation: `isinstance(item, str)`, max 200 chars, strip control characters
  - Add `_sanitize_entity_list()` in summary_generator: strip `{}`  braces before `.format()` injection
- **Tests:** Overlong entities truncated, control chars stripped, format-string injection does not crash
- **Close:** #34 as duplicate of #37 (or vice versa)

---

## Dependency Order

```
Phase 1 (verify #8)
  ↓
Phase 2 (#7, #12) — independent quick fixes
  ↓
Phase 3 (#5, #6, #10, #14) — validation cluster
  ↓
Phase 4 (#11, #13) ──────┐
Phase 5 (#9)  ────────────┤  (parallel — no shared files)
  ↓                       ↓
Phase 6a (#33/#36) — base_llm_client.py changes
  ↓
Phase 6b (#34/#37) — depends on 6a (same file)
```

Phases 4 and 5 can run in parallel. Phase 6a must precede 6b.

---

## TDD Protocol Per Issue

1. Write failing tests → commit `test: [issue-N] add failing tests for <desc>`
2. Implement fix → commit `fix: [issue-N] <desc>`
3. Run full suite (`pytest tests/`) → verify no regressions
4. Push branch, open PR referencing issue numbers
