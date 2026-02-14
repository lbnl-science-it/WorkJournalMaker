# Cluster A: Quick Fixes — Implementation Plan

## Overview

Five quick-fix improvements from `improvements.md` that have no cross-dependencies and can each be completed in a single atomic commit. Each fix follows TDD where applicable.

**Source:** `improvements.md` items #12, #15, #20, #21, #22
**Branch:** `improvements/code-review`

---

## Step 1: Fix Broken Error Logging in Settings API

**Issue:** `web/api/settings.py` has 11 instances of a broken error logging pattern:

```python
logger.logger.error if logger else print(f"Failed to ...")
```

This is a conditional *expression*, not a conditional *statement*. `logger.logger.error` evaluates as a truthy method reference but is never *called*. The error message is silently discarded.

**Scope:** 11 occurrences in `web/api/settings.py` (lines 62, 77, 315, 342, 537, 552, 567, 588, 631, 648, and line 62 has a double `if logger else print` variant).

**TDD Approach:**
1. Write a test that triggers an error in a settings endpoint and verifies logging occurs
2. Run test — confirm it fails (error swallowed)
3. Fix all 11 instances to use proper `if/else` statements
4. Run test — confirm it passes

### Prompt

```text
Fix broken error logging in web/api/settings.py.

There are 11 instances of this broken pattern:
  logger.logger.error if logger else print(f"message")
and one variant with a doubled condition on line 62:
  logger.logger.error if logger else print if logger else print(f"message")

These are conditional expressions, not statements. The method reference
logger.logger.error is truthy so the error string is never logged or printed.

TDD steps:
1. Create tests/test_settings_api_logging.py
2. Write a test that mocks the settings service to raise an exception,
   calls the endpoint, and asserts the error was logged (check logger.logger.error
   was called with matching string)
3. Run the test — it should FAIL because the current code never calls the logger
4. Fix all 11 broken logging lines in web/api/settings.py. Replace each with:
     if logger:
         logger.logger.error(f"message")
     else:
         print(f"message")
5. Run the test — it should PASS
6. Commit with message: "Fix broken error logging in settings API"

Do NOT change anything else in the file. Only fix the logging pattern.
```

---

## Step 2: Fix Hardcoded WebSocket URL

**Issue:** `web/static/js/websocket-client.js:9` hardcodes `ws://localhost:8000` as the default WebSocket URL. The server uses a configurable port range (8000-8099), so WebSocket connections break silently on any port other than 8000.

**Scope:** Single file, single line change.

**TDD Approach:**
1. Write a JS-level test or a Python integration test that verifies the WebSocket client derives its URL from the current host
2. Fix the default parameter
3. Verify

### Prompt

```text
Fix the hardcoded WebSocket URL in web/static/js/websocket-client.js.

Line 9 currently reads:
  constructor(baseUrl = 'ws://localhost:8000') {

The server's port is configurable via --port-range (default 8000-8099).
If the server starts on port 8001+, WebSocket connections fail silently.

TDD steps:
1. Create tests/test_websocket_url.py
2. Write a test that reads web/static/js/websocket-client.js and asserts:
   - The constructor does NOT contain a hardcoded port number
   - The default uses window.location (e.g., via regex match)
3. Run the test — it should FAIL
4. Change line 9 to derive the URL from the browser's current location:
     constructor(baseUrl = `ws://${window.location.host}`) {
   Also handle wss:// for HTTPS by checking window.location.protocol:
     const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
     constructor(baseUrl = `${wsProtocol}//${window.location.host}`) {
   Note: since this is a default parameter, the protocol check needs to
   be done in the constructor body instead. Refactor as:
     constructor(baseUrl = null) {
         if (!baseUrl) {
             const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
             baseUrl = `${wsProtocol}//${window.location.host}`;
         }
         this.baseUrl = baseUrl;
         ...
5. Run the test — it should PASS
6. Commit with message: "Derive WebSocket URL from current host"
```

---

## Step 3: Remove Build Artifacts from Git Tracking

**Issue:** `build/WorkJournalMaker/` contains 9 tracked files (54 MB total) including `.pkg`, `.pyz`, and `.toc` files. These are PyInstaller outputs that are reproducible and bloat the repo. The `.gitignore` already has `build/` but these files were added before that rule.

**Scope:** `git rm --cached` on the build directory. No code changes.

**No TDD needed** — this is a version control cleanup with no runtime behavior.

### Prompt

```text
Remove build artifacts from git tracking.

The build/ directory contains 54 MB of PyInstaller output that is tracked
in git despite .gitignore having a build/ entry. These files were added
before the gitignore rule existed.

Steps:
1. Verify .gitignore already contains "build/" (it does, on line 139)
2. Run: git rm -r --cached build/
3. Commit with message: "Remove tracked build artifacts from git"

Do NOT delete the actual build/ directory from disk — only untrack it.
Do NOT modify .gitignore (the rule already exists).
```

---

## Step 4: Delete Accidental Empty File

**Issue:** A zero-byte file named `t` exists at the project root. It is tracked in git and serves no purpose.

**Scope:** Delete one file.

**No TDD needed** — removing an empty file.

### Prompt

```text
Delete the accidental empty file 't' from the repository root.

Steps:
1. Verify the file exists and is empty: ls -la t
2. Run: git rm t
3. Commit with message: "Remove accidental empty file"
```

---

## Step 5: Remove Debug Artifacts from Version Control

**Issue:** Several debugging artifacts are tracked in git that should not be in the repository:
- `robust_settings_test_results.json` — test output
- `mcp_fix.txt` — debugging notes
- `mcp_server_diagnosis.txt` — debugging notes
- `run_settings_persistence_tests.py` — one-off test script
- `config_fix.md` — debugging notes
- `debug_scripts/debug_database_test_results.json` — test output

**Scope:** Remove files from tracking, update `.gitignore`.

**No TDD needed** — version control cleanup.

### Prompt

```text
Remove debug artifacts from version control.

The following tracked files are debugging artifacts that don't belong
in the repository:

- robust_settings_test_results.json (test output)
- mcp_fix.txt (debug notes)
- mcp_server_diagnosis.txt (debug notes)
- run_settings_persistence_tests.py (one-off test script)
- config_fix.md (debug notes)
- debug_scripts/debug_database_test_results.json (test output)

Steps:
1. Remove files from git tracking:
   git rm robust_settings_test_results.json mcp_fix.txt \
     mcp_server_diagnosis.txt run_settings_persistence_tests.py \
     config_fix.md debug_scripts/debug_database_test_results.json
2. Add patterns to .gitignore to prevent re-adding:
   - Under "# Debug and test artifacts" section, add:
     mcp_fix.txt
     mcp_server_diagnosis.txt
     *_test_results.json
     config_fix.md
3. Commit with message: "Remove debug artifacts from version control"
```

---

## Summary

| Step | Fix | TDD? | Files Changed |
|------|-----|------|---------------|
| 1 | Broken error logging | Yes | `web/api/settings.py`, new test |
| 2 | Hardcoded WebSocket URL | Yes | `web/static/js/websocket-client.js`, new test |
| 3 | Build artifacts tracked | No | git-only (untrack `build/`) |
| 4 | Empty file `t` | No | git-only (delete `t`) |
| 5 | Debug artifacts tracked | No | git-only + `.gitignore` update |
