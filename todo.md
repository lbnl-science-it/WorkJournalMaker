# Issue #60 — Fix Pre-existing Test Failures

**Plan:** `plan.md`
**Branch:** `fix/issue-60-test-failures`
**Baseline:** 54 failed + 18 errors = 72 broken (in scope) | 169 failed full suite

## Phase 1: Async Fixture Decorator Fixes (APPROVED)

- [ ] **Step 1.1:** Fix work_week async test fixtures ([#73](https://github.com/lbnl-science-it/WorkJournalMaker/issues/73))
- [ ] **Step 1.2:** Fix calendar async test fixtures ([#74](https://github.com/lbnl-science-it/WorkJournalMaker/issues/74))
- [ ] **Step 1.3:** Fix web integration async test fixtures ([#75](https://github.com/lbnl-science-it/WorkJournalMaker/issues/75))
- [ ] **Step 1.4:** Phase 1 verification + decision gate

## Decision Gate

After Phase 1, evaluate results:
- **>80% pass** → proceed with Phase 2
- **50-80% pass** → selectively fix, delete the rest
- **<50% pass** → close Phase 2 issues, rewrite from scratch

## Phase 2: Contract Mismatch Fixes (GATED — pending Phase 1 results)

- [ ] **Step 2.1:** WorkWeekConfig validation test contracts ([#76](https://github.com/lbnl-science-it/WorkJournalMaker/issues/76)) — 11 failures
- [ ] **Step 2.2:** Work week settings service test contract ([#77](https://github.com/lbnl-science-it/WorkJournalMaker/issues/77)) — 1 failure
- [ ] **Step 2.3:** Build config test contracts ([#78](https://github.com/lbnl-science-it/WorkJournalMaker/issues/78)) — 2 failures
- [ ] **Step 2.4:** Settings persistence test setup ([#79](https://github.com/lbnl-science-it/WorkJournalMaker/issues/79)) — 6 failures
- [ ] **Step 3.1:** Full scope verification ([#80](https://github.com/lbnl-science-it/WorkJournalMaker/issues/80))
- [ ] **Step 3.2:** Update and close issue #60
