# WorkJournalMaker — Issue Triage & Execution Plan

Full design: [docs/superpowers/specs/2026-05-08-issue-triage-design.md](docs/superpowers/specs/2026-05-08-issue-triage-design.md)

## Cluster T1: Re-Audit & Fix Test Isolation

- [x] Re-run isolation audit against current codebase (post-DB-relocation)
- [x] [#118](https://github.com/lbnl-science-it/WorkJournalMaker/issues/118) — Fix test_calendar_api_date_range: reads real production DB
- [x] [#116](https://github.com/lbnl-science-it/WorkJournalMaker/issues/116) — Clean up stale DB files after migration verification (files already removed)
- [x] [#113](https://github.com/lbnl-science-it/WorkJournalMaker/issues/113) — Rewrite live-server tests to use TestClient with isolation
- [x] Fix remaining DANGEROUS files identified by re-audit
- [x] **GATE:** No test writes to production data or leaves side effects

## Cluster T2: Test Coverage Rewrite

- [x] [#81](https://github.com/lbnl-science-it/WorkJournalMaker/issues/81) — Fix stale test assertions and delete broken tests with redundant coverage
- [x] **GATE:** Services have tests covering actual public APIs, properly isolated, passing

## Cluster S: Security Hardening

### Critical
- [x] [#87](https://github.com/lbnl-science-it/WorkJournalMaker/issues/87) — No authentication on any web API endpoint
- [x] [#88](https://github.com/lbnl-science-it/WorkJournalMaker/issues/88) — Multiple XSS vectors via innerHTML
- [x] [#89](https://github.com/lbnl-science-it/WorkJournalMaker/issues/89) — No CSRF protection on state-changing API calls

### High
- [ ] [#90](https://github.com/lbnl-science-it/WorkJournalMaker/issues/90) — Path traversal via validate-path endpoint
- [ ] [#91](https://github.com/lbnl-science-it/WorkJournalMaker/issues/91) — No security response headers
- [ ] [#92](https://github.com/lbnl-science-it/WorkJournalMaker/issues/92) — CDN script without Subresource Integrity
- [ ] [#93](https://github.com/lbnl-science-it/WorkJournalMaker/issues/93) — Unescaped data in inline onclick attributes

### Medium
- [ ] [#94](https://github.com/lbnl-science-it/WorkJournalMaker/issues/94) — Prompt injection via unsanitized journal content
- [ ] [#95](https://github.com/lbnl-science-it/WorkJournalMaker/issues/95) — Unrestricted base_path enables arbitrary file write
- [ ] [#96](https://github.com/lbnl-science-it/WorkJournalMaker/issues/96) — Information disclosure via error messages
- [ ] [#97](https://github.com/lbnl-science-it/WorkJournalMaker/issues/97) — CORS misconfiguration
- [ ] [#98](https://github.com/lbnl-science-it/WorkJournalMaker/issues/98) — GCP project ID hardcoded in source code
- [ ] [#99](https://github.com/lbnl-science-it/WorkJournalMaker/issues/99) — Client-only input validation
- [ ] [#110](https://github.com/lbnl-science-it/WorkJournalMaker/issues/110) — Bulk update settings always returns HTTP 200

### Low
- [ ] [#100](https://github.com/lbnl-science-it/WorkJournalMaker/issues/100) — Full file_path exposed in API responses
- [ ] [#101](https://github.com/lbnl-science-it/WorkJournalMaker/issues/101) — Full LLM request body logged at DEBUG level
- [ ] [#102](https://github.com/lbnl-science-it/WorkJournalMaker/issues/102) — raw_response stores full error strings
- [ ] [#103](https://github.com/lbnl-science-it/WorkJournalMaker/issues/103) — Timezone accepts arbitrary strings
- [ ] [#104](https://github.com/lbnl-science-it/WorkJournalMaker/issues/104) — WebSocket endpoints without auth/origin check
- [ ] [#105](https://github.com/lbnl-science-it/WorkJournalMaker/issues/105) — showToast passes error_message via innerHTML
- [ ] [#106](https://github.com/lbnl-science-it/WorkJournalMaker/issues/106) — Test/debug pages accessible in production
- [ ] [#107](https://github.com/lbnl-science-it/WorkJournalMaker/issues/107) — No content size limit on entry POST
- [ ] [#108](https://github.com/lbnl-science-it/WorkJournalMaker/issues/108) — Scheduler accepts zero/negative intervals

- [ ] **GATE:** Critical and high resolved; medium/low resolved or consciously accepted

## Cluster U: UI Bugs

- [ ] [#30](https://github.com/lbnl-science-it/WorkJournalMaker/issues/30) — Changing default work week fails
- [ ] [#26](https://github.com/lbnl-science-it/WorkJournalMaker/issues/26) — Broken Today Button
- [ ] [#27](https://github.com/lbnl-science-it/WorkJournalMaker/issues/27) — Calendar preview of journal entry cuts off
- [ ] [#28](https://github.com/lbnl-science-it/WorkJournalMaker/issues/28) — Missized Calendar
- [ ] [#32](https://github.com/lbnl-science-it/WorkJournalMaker/issues/32) — Save button hidden when editor window is at the bottom
- [ ] **GATE:** Basic user workflow works end-to-end (verified via Playwright)

## Cluster D: Desktop Packaging

- [ ] [#72](https://github.com/lbnl-science-it/WorkJournalMaker/issues/72) — Step 12: Build Automation Testing (CI/CD simulation)
- [ ] Step 13: Release Management and Distribution
- [ ] Step 14: End-to-End Integration Testing

## Cluster R: Package Restructure

- [ ] Move 15 root-level core modules into `workjournalmaker/` package (gated on Cluster S completion)
- [ ] Design spec: `docs/superpowers/specs/2026-05-08-root-cleanup-design.md` (Phase 2 section)
