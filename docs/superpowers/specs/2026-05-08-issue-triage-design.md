# Issue Triage & Execution Plan

**Date:** 2026-05-08
**Scope:** All 33 open GitHub issues
**Approach:** Clustered with decision gates (proven pattern from improvement metaplan)

## Guiding Principle

Test foundation first. A reliable test suite is the prerequisite for safe work
on security and features. The desktop app coordinates with the web app, so
stabilizing the web app is prerequisite work for desktop packaging — not a
competing priority.

## Cluster Structure

```
T1: Re-Audit & Fix Test Isolation
    ↓ (gate: "test suite trustworthy?")
T2: Test Coverage Rewrite (#81)
    ↓ (gate: "coverage sufficient?")
S:  Security Hardening (#87–#108)
    ↓ (gate: "deploy-ready?")
U:  UI Bugs (#26–#32)
    ↓ (gate: "web app locked?")
D:  Desktop Packaging (#72, Steps 13–14)
```

T1 → T2 → S → U → D is the critical path. Each cluster has a decision gate
at the end where we assess whether to proceed, adjust scope, or re-plan.

---

## Cluster T1: Re-Audit & Fix Test Isolation

**Goal:** Determine which of the April audit's 31 flagged test files are still
problematic after the DB relocation (#114, #119, #122), then fix what remains.

**Scope:**

1. Re-run the isolation audit against the current codebase. The April audit
   identified issues based on `DatabaseManager()` defaulting to
   `./web/journal_index.db` — the DB relocation changed that behavior, so
   some findings may be obsolete.
2. Incorporate the three known open test issues:
   - **#118** — `test_calendar_api_date_range` reads real production DB
   - **#116** — Clean up stale DB files after migration verification
   - **#113** — Rewrite live-server tests to use TestClient with isolation
3. Fix all files that the re-audit flags as DANGEROUS (writes to production data).
4. Assess RISKY files (read-only production access) and decide case-by-case.

**Decision gate:** Can we run `pytest` with confidence that no test writes to
production data or leaves side effects?

The gate does NOT require full coverage or all tests passing. Just isolation —
tests can fail, but they must fail safely.

---

## Cluster T2: Test Coverage Rewrite (#81)

**Goal:** Write proper test coverage for the three areas identified in the #60
post-mortem as having fundamentally broken tests: work week, calendar, and web
integration services.

**Context:** The #60 decision gate found that existing tests in these areas
were never validated against production code — they tested stale API signatures
and removed model columns. The decision was "delete and rewrite, don't patch."

**Scope:**

- Rewrite tests for work week services (settings, database sync, compatibility)
- Rewrite tests for calendar services (calendar service, API endpoints)
- Rewrite tests for web integration (entry manager, summarization pipeline)
- All new tests must use proper isolation (patterns established in T1)

**Out of scope:** Tests for CLI modules, LLM clients, file discovery — those
already have verified-safe coverage per the April audit.

**Decision gate:** Do the work week, calendar, and web integration services
have tests that cover their actual public APIs, use proper isolation, and pass?
Define a concrete coverage target when scoping the rewrite.

---

## Cluster S: Security Hardening (#87–#108)

**Goal:** Fix the 22 security issues from the April audit, working from highest
to lowest severity. By this point, T1 and T2 will have provided a reliable test
suite as a safety net.

### Critical (3)

| Issue | Title |
|-------|-------|
| #87   | No authentication on any web API endpoint |
| #88   | Multiple XSS vectors via innerHTML with unsanitized content |
| #89   | No CSRF protection on state-changing API calls |

### High (4)

| Issue | Title |
|-------|-------|
| #90   | Path traversal via filesystem validate-path endpoint |
| #91   | No security response headers (CSP, X-Frame-Options, etc.) |
| #92   | CDN script loaded without Subresource Integrity |
| #93   | Unescaped data in inline onclick attributes |

### Medium (6)

| Issue | Title |
|-------|-------|
| #94   | Prompt injection via unsanitized journal content in LLM calls |
| #95   | Unrestricted base_path setting enables arbitrary file write |
| #96   | Information disclosure via error messages and health endpoints |
| #97   | CORS misconfiguration — allow_headers wildcard with credentials |
| #98   | GCP project ID hardcoded in source code |
| #99   | Client-only input validation bypassed by direct API calls |

### Low (9)

| Issue | Title |
|-------|-------|
| #100  | Full file_path exposed in API responses |
| #101  | Full LLM request body logged at DEBUG level |
| #102  | raw_response stores full error strings with internal details |
| #103  | work_week.timezone accepts arbitrary strings without validation |
| #104  | WebSocket endpoints accept connections without auth or origin check |
| #105  | Utils.showToast passes server error_message via innerHTML |
| #106  | Test/debug pages accessible in production builds |
| #107  | No content size limit on entry content POST endpoint |
| #108  | Scheduler config accepts zero/negative intervals (DoS risk) |

**Internal ordering notes:**

- #87 (auth) is the natural starting point — many other issues become less
  severe once authentication exists
- #88 and #93 (XSS/onclick) are closely related and can be bundled
- #91 (security headers) is a one-shot middleware change that mitigates
  several downstream issues

**Decision gate:** Are the critical and high severity issues resolved? Are
medium/low issues either resolved or consciously accepted as known risks for
the current deployment context?

The gate allows proceeding to UI bugs even if some low-severity risks are
accepted rather than fixed.

---

## Cluster U: UI Bugs

**Goal:** Fix the 5 open user-facing bugs. By this point, we have reliable
tests (T1/T2) and a secure backend (S), so these fixes carry low risk.

| Issue | Title |
|-------|-------|
| #30   | Changing default work week fails |
| #26   | Broken Today button |
| #27   | Calendar preview of journal entry cuts off |
| #28   | Missized calendar |
| #32   | Save button hidden when editor window is at the bottom |

**Internal ordering:** #30 first (functional bug preventing a core feature),
then the calendar cluster (#26, #27, #28) which likely share root causes,
then #32.

**Verification:** Playwright MCP is available for browser-based UI testing.
Each fix should be verified by interacting with the running app, not just
by test assertions.

**Decision gate:** Does the web app work correctly for the basic user workflow:
view calendar, navigate to today, preview an entry, edit and save it, change
work week settings?

---

## Cluster D: Desktop Packaging

**Goal:** Complete the remaining desktop packaging steps once the web app is
locked down.

| Item | Title |
|------|-------|
| #72  | Step 12: Build Automation Testing (CI/CD simulation) |
| —    | Step 13: Release Management and Distribution |
| —    | Step 14: End-to-End Integration Testing |

**Prerequisite:** Clusters T1, T2, S, and U all pass their gates. The desktop
app wraps a stable, secure, tested web app.

**Note:** The existing `desktop/build_system` code has never produced a working
build. This cluster may require re-scoping once we get to it — Steps 12–14
assume Steps 1–11 produced a functional baseline, which should be verified
before proceeding.

---

## Housekeeping

- **#67** was closed — remove from `todo.md`
- **#110** (settings endpoint returns 200) fits naturally into Cluster S
  alongside #99 (server-side validation) — group it there
- Update `todo.md` to reflect cluster structure
- Gate decisions are recorded inline in this document as clusters complete

---

## Progress

| Cluster | Status | Gate Result |
|---------|--------|-------------|
| T1      | Not started | — |
| T2      | Not started | — |
| S       | Not started | — |
| U       | Not started | — |
| D       | Not started | — |
