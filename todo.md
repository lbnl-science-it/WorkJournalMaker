# Issue #60 — Fix Pre-existing Test Failures (CLOSED)

**Plan:** `plan.md`
**Branch:** `fix/issue-60-test-failures`
**Result:** 6 tests recovered, Phase 2 cancelled, rewrite filed as #81

## Phase 1: Async Fixture Decorator Fixes (COMPLETE)

- [x] **Step 1.1:** Fix work_week async test fixtures ([#73](https://github.com/lbnl-science-it/WorkJournalMaker/issues/73)) — 6 tests recovered
- [x] **Step 1.2:** Calendar tests — no async fixture issues found ([#74](https://github.com/lbnl-science-it/WorkJournalMaker/issues/74))
- [x] **Step 1.3:** Web tests — no async fixture issues found ([#75](https://github.com/lbnl-science-it/WorkJournalMaker/issues/75))
- [x] **Step 1.4:** Decision gate — 11% recovery, below 50% threshold

## Decision Gate Result: DO NOT PROCEED

- Recovery rate: 11% (6 of 55 broken tests)
- Root cause: tests were never validated against production code
- Action: Phase 2 closed, rewrite issue filed

## Phase 2: CANCELLED

- [x] ~~#76, #77, #78, #79, #80~~ — closed, superseded by [#81](https://github.com/lbnl-science-it/WorkJournalMaker/issues/81)
