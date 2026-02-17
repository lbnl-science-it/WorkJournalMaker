# Cluster A: Quick Fixes — Implementation Tracker

**Plan:** `plan.md`
**Source:** `improvements.md` items #12, #15, #20, #21, #22
**Branch:** `improvements/code-review`

## Steps

- [x] **Step 1:** Fix broken error logging in `web/api/settings.py` (11 instances) — TDD ([#41](https://github.com/lbnl-science-it/WorkJournalMaker/issues/41))
- [x] **Step 2:** Fix hardcoded WebSocket URL in `web/static/js/websocket-client.js` — TDD ([#42](https://github.com/lbnl-science-it/WorkJournalMaker/issues/42))
- [x] **Step 3:** Remove build artifacts from git tracking (`build/`, 54 MB) ([#43](https://github.com/lbnl-science-it/WorkJournalMaker/issues/43))
- [x] **Step 4:** Delete accidental empty file `t` ([#44](https://github.com/lbnl-science-it/WorkJournalMaker/issues/44))
- [x] **Step 5:** Remove debug artifacts from version control (6 files + `.gitignore` update) ([#45](https://github.com/lbnl-science-it/WorkJournalMaker/issues/45))
