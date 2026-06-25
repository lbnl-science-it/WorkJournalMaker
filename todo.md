# WorkJournalMaker — Issue Triage & Execution Plan

Full design: [docs/superpowers/specs/2026-05-08-issue-triage-design.md](docs/superpowers/specs/2026-05-08-issue-triage-design.md)

## Cluster T1: Re-Audit & Fix Test Isolation

- [x] Re-run isolation audit against current codebase (post-DB-relocation)
- [x] [#118](https://github.com/lbnl-science-it/WorkJournalMaker/issues/118) — Fix test_calendar_api_date_range: reads real production DB
- [x] [#116](https://github.com/lbnl-science-it/WorkJournalMaker/issues/116) — Clean up stale DB files after migration verification (files already removed)
- [x] [#113](https://github.com/lbnl-science-it/WorkJournalMaker/issues/113) — Remove live-server tests that corrupt worklog files
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
- [x] [#90](https://github.com/lbnl-science-it/WorkJournalMaker/issues/90) — Path traversal via validate-path endpoint
- [x] [#91](https://github.com/lbnl-science-it/WorkJournalMaker/issues/91) — No security response headers
- [x] [#92](https://github.com/lbnl-science-it/WorkJournalMaker/issues/92) — CDN script without Subresource Integrity
- [x] [#93](https://github.com/lbnl-science-it/WorkJournalMaker/issues/93) — Unescaped data in inline onclick attributes

### Medium
- [x] [#94](https://github.com/lbnl-science-it/WorkJournalMaker/issues/94) — Prompt injection via unsanitized journal content
- [x] [#95](https://github.com/lbnl-science-it/WorkJournalMaker/issues/95) — Unrestricted base_path enables arbitrary file write
- [x] [#96](https://github.com/lbnl-science-it/WorkJournalMaker/issues/96) — Information disclosure via error messages
- [x] [#97](https://github.com/lbnl-science-it/WorkJournalMaker/issues/97) — CORS misconfiguration
- [x] [#98](https://github.com/lbnl-science-it/WorkJournalMaker/issues/98) — GCP project ID hardcoded in source code
- [x] [#99](https://github.com/lbnl-science-it/WorkJournalMaker/issues/99) — Client-only input validation
- [ ] [#110](https://github.com/lbnl-science-it/WorkJournalMaker/issues/110) — Bulk update settings always returns HTTP 200

### Low
- [x] [#100](https://github.com/lbnl-science-it/WorkJournalMaker/issues/100) — Full file_path exposed in API responses
- [x] [#101](https://github.com/lbnl-science-it/WorkJournalMaker/issues/101) — Full LLM request body logged at DEBUG level
- [x] [#102](https://github.com/lbnl-science-it/WorkJournalMaker/issues/102) — raw_response stores full error strings
- [x] [#103](https://github.com/lbnl-science-it/WorkJournalMaker/issues/103) — Timezone accepts arbitrary strings
- [x] [#104](https://github.com/lbnl-science-it/WorkJournalMaker/issues/104) — WebSocket endpoints without auth/origin check
- [x] [#105](https://github.com/lbnl-science-it/WorkJournalMaker/issues/105) — showToast passes error_message via innerHTML
- [x] [#106](https://github.com/lbnl-science-it/WorkJournalMaker/issues/106) — Test/debug pages accessible in production
- [x] [#107](https://github.com/lbnl-science-it/WorkJournalMaker/issues/107) — No content size limit on entry POST
- [x] [#108](https://github.com/lbnl-science-it/WorkJournalMaker/issues/108) — Scheduler accepts zero/negative intervals

### Post-Triage Security Fixes
- [x] [#146](https://github.com/lbnl-science-it/WorkJournalMaker/issues/146) — Validate LLM output schema for analyze_content responses
- [x] [#147](https://github.com/lbnl-science-it/WorkJournalMaker/issues/147) — Separate system/user messages in LLM provider clients
- [x] [#150](https://github.com/lbnl-science-it/WorkJournalMaker/issues/150) — Missing CSRF headers in calendar.js and settings.js fetch() calls
- [x] [#152](https://github.com/lbnl-science-it/WorkJournalMaker/issues/152) — Add cache-busting for static JavaScript assets

- [ ] **GATE:** Critical and high resolved; medium/low resolved or consciously accepted (#110 is the sole remaining item)

## Cluster U: UI Bugs

- [ ] [#30](https://github.com/lbnl-science-it/WorkJournalMaker/issues/30) — Changing default work week fails
- [x] [#26](https://github.com/lbnl-science-it/WorkJournalMaker/issues/26) — Broken Today Button
- [x] [#156](https://github.com/lbnl-science-it/WorkJournalMaker/issues/156) — Calendar 'Today' button navigates to wrong date after ~5pm (timezone fix)
- [ ] [#27](https://github.com/lbnl-science-it/WorkJournalMaker/issues/27) — Calendar preview of journal entry cuts off
- [ ] [#28](https://github.com/lbnl-science-it/WorkJournalMaker/issues/28) — Missized Calendar
- [ ] [#32](https://github.com/lbnl-science-it/WorkJournalMaker/issues/32) — Save button hidden when editor window is at the bottom
- [ ] **GATE:** Basic user workflow works end-to-end (verified via Playwright)

## Housekeeping

- [x] [#126](https://github.com/lbnl-science-it/WorkJournalMaker/issues/126) — Review and clean up debug/utility scripts in tests/
- [ ] [#133](https://github.com/lbnl-science-it/WorkJournalMaker/issues/133) — ErrorCategory enum missing DATABASE_ERROR and FILE_ACCESS_ERROR members

## Cluster D: Desktop Packaging

- [ ] [#72](https://github.com/lbnl-science-it/WorkJournalMaker/issues/72) — Step 12: Build Automation Testing (CI/CD simulation)
- [ ] Step 13: Release Management and Distribution
- [ ] Step 14: End-to-End Integration Testing

## Cluster R: Package Restructure

- [ ] Move 15 root-level core modules into `workjournalmaker/` package (gated on Clusters S and U completion)
- [ ] Design spec: `docs/superpowers/specs/2026-05-08-root-cleanup-design.md` (Phase 2 section)
