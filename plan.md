# Cluster D: Package Structure — Implementation Plan

**Source:** `improvements.md` items #13, #19
**Branch:** `improvements/code-review`
**Depends on:** Cluster B (complete)

## Problem Summary

The project has no `pyproject.toml`, no root `__init__.py`, and no `conftest.py`.
Root-level CLI modules (`config_manager.py`, `logger.py`, etc.) are not importable
as a package. Every file under `web/`, `tests/`, `scripts/`, and `debug_scripts/`
works around this with `sys.path.append`/`sys.path.insert` — 84 occurrences across
83 files. These hacks are fragile, order-dependent, and cause `sys.path` to grow
indefinitely during long-running server processes.

## Design Decision

**Flat layout with `pyproject.toml` at project root.**

The project already has `web/`, `desktop/`, `scripts/`, and `build_system/` as
proper sub-packages with `__init__.py`. The root CLI modules are the only
loose files. A `pyproject.toml` with a flat layout makes the project root
discoverable via `pip install -e .` without moving any files. This is the
minimum-disruption approach.

## Scope

| Location | Files | sys.path calls |
|----------|-------|----------------|
| `web/` | 18 | 18 |
| `tests/` | 57 | 57 |
| `scripts/` | 4 | 4 |
| `debug_scripts/` | 2 | 3 |
| root (`reset_database_with_fix.py`) | 1 | 1 |
| **Total** | **83** | **84** (one file has 2) |

### What the sys.path hacks resolve

All 84 calls exist for the same reason: to make root-level modules importable
(`config_manager`, `logger`, `file_discovery`, `llm_data_structures`, etc.).

One special case: `web/models/journal.py` appends `web/`'s parent to import
`from utils.timezone_utils`. After the fix, this becomes
`from web.utils.timezone_utils`.

## Implementation Steps

Steps are ordered so the test suite stays green after each commit.

---

### Step 1: Add pyproject.toml and install in editable mode

**Scope:** Create `pyproject.toml`, add root `conftest.py`, and install the
project in editable mode in the `WorkJournal` pyenv environment.

**Why first:** Purely additive — the sys.path hacks still work alongside the
editable install. This establishes the foundation that makes all subsequent
removals safe.

**Files touched:**
- `pyproject.toml` (new)
- `conftest.py` (new — empty, ensures pytest discovers root as package)

```text
PROMPT:

Context: We are working on the WorkJournalMaker project on branch
`improvements/code-review`. There is no pyproject.toml, no setup.py,
and no conftest.py. Root-level modules (config_manager.py, logger.py,
file_discovery.py, etc.) sit at the project root but are not part of
a Python package. 83 files use sys.path.append/insert hacks to import
them.

The project uses a pyenv virtualenv called `WorkJournal`. Dependencies
are listed in `requirements.txt`.

Task:

1. Create `pyproject.toml` at the project root with:
   - Build system: setuptools
   - Project name: workjournalmaker
   - Python requirement: >=3.8
   - A `[tool.setuptools.packages.find]` section that includes
     root-level .py modules plus the existing sub-packages (web,
     desktop, scripts, build_system, debug_scripts)
   - A `[tool.pytest.ini_options]` section with:
     testpaths = ["tests"]
     pythonpath = ["."]
   - Dependencies from requirements.txt

2. Create an empty `conftest.py` at the project root with ABOUTME
   comments. This ensures pytest treats the root as importable.

3. Run `pip install -e .` in the WorkJournal pyenv to install the
   project in editable mode.

4. Verify the install works:
   - `python -c "import config_manager; print('OK')"`
   - `python -c "from web.app import create_logger_with_config; print('OK')"`

5. Run the existing test suite to confirm nothing broke (the sys.path
   hacks are still present — they just become redundant).

6. Commit with a descriptive message.
```

---

### Step 2: Remove sys.path hacks from web/ modules (18 files)

**Scope:** Remove all `sys.path.append`/`sys.path.insert` calls and their
associated `import sys` / `from pathlib import Path` lines (when no longer
used) from the 18 production files under `web/`.

**Why second:** Production code first — this is the most important batch
because these run in long-lived server processes where sys.path accumulation
is worst.

**Special case:** `web/models/journal.py` needs its import changed from
`from utils.timezone_utils import ...` to
`from web.utils.timezone_utils import ...`.

**Files touched:** 18 files under `web/`

```text
PROMPT:

Context: The project now has `pyproject.toml` and is installed in editable
mode. Root-level modules are importable without sys.path manipulation.

Task:

1. For each of these 18 files, remove the `sys.path.append(...)` line
   and its comment. If `sys` and `Path` are no longer used after removal,
   remove those imports too:

   web/app.py
   web/middleware.py
   web/models/journal.py (SPECIAL: also change
     `from utils.timezone_utils import ...` to
     `from web.utils.timezone_utils import ...`)
   web/api/calendar.py
   web/api/entries.py
   web/api/health.py
   web/api/settings.py
   web/api/summarization.py
   web/api/sync.py
   web/services/base_service.py
   web/services/calendar_service.py
   web/services/entry_manager.py
   web/services/scheduler.py
   web/services/settings_service.py
   web/services/sync_service.py
   web/services/web_summarizer.py
   web/services/work_week_service.py
   web/migrations/001_add_work_week_settings.py

2. Run `python -c "from web.app import create_logger_with_config"` to
   verify imports still resolve.

3. Run the test suite to confirm nothing broke.

4. Commit with a descriptive message.
```

---

### Step 3: Remove sys.path hacks from tests/ (57 files)

**Scope:** Remove all `sys.path.append`/`sys.path.insert` calls from the
57 test files. Clean up unused `sys`/`Path` imports where possible.

**Why third:** Test files are the largest batch. With `pythonpath = ["."]`
in pyproject.toml's pytest config, pytest automatically adds the project
root to sys.path, making all test imports work.

**Files touched:** 57 files under `tests/`

```text
PROMPT:

Context: The project has `pyproject.toml` with
`[tool.pytest.ini_options] pythonpath = ["."]`. Root modules are
importable. The web/ production code has already been cleaned up.

Task:

1. For ALL test files under `tests/` that contain
   `sys.path.append(...)` or `sys.path.insert(...)`, remove those
   lines and their comments. If `sys` and/or `Path` (from pathlib)
   are no longer used after removal, remove those imports too.

   There are 57 files to clean. The change is mechanical: delete
   the sys.path line and its comment, then check if sys/Path are
   still used elsewhere in the file.

2. Run the test suite to confirm nothing broke.

3. Commit with a descriptive message.
```

---

### Step 4: Remove sys.path hacks from scripts/, debug_scripts/, and root (7 files)

**Scope:** Clean up the remaining 7 files: 4 in `scripts/`, 2 in
`debug_scripts/`, and 1 at root (`reset_database_with_fix.py`).

**Why last:** Smallest batch, lowest risk.

**Files touched:**
- `scripts/build.py`
- `scripts/build_clean.py`
- `scripts/build_quick.py`
- `scripts/build_test.py`
- `debug_scripts/debug_settings_integration.py`
- `debug_scripts/debug_database_write.py` (has 2 sys.path calls)
- `reset_database_with_fix.py`

```text
PROMPT:

Context: The project has `pyproject.toml` and is installed in editable
mode. Web/ and tests/ have been cleaned up already.

Task:

1. Remove `sys.path.insert`/`sys.path.append` calls from these 7 files:
   - scripts/build.py
   - scripts/build_clean.py
   - scripts/build_quick.py
   - scripts/build_test.py
   - debug_scripts/debug_settings_integration.py
   - debug_scripts/debug_database_write.py (has 2 calls)
   - reset_database_with_fix.py

   Clean up unused sys/Path imports as before.

2. Run the test suite to confirm nothing broke.

3. Verify final state:
   grep -r "sys.path.append\|sys.path.insert" --include="*.py" | \
     grep -v ".pyenv" | grep -v "venv"
   Should return ZERO results.

4. Commit with a descriptive message.
```

---

## Risk Assessment

| Step | Risk | Mitigation |
|------|------|------------|
| 1 - Add pyproject.toml | None (additive) | Editable install coexists with sys.path hacks |
| 2 - Clean web/ | Low | 18 files, same mechanical edit |
| 3 - Clean tests/ | Low | 57 files, same mechanical edit. pytest pythonpath config handles it |
| 4 - Clean scripts/ | None | 7 files, smallest batch |

## Verification

After all steps, run:
```bash
# No sys.path hacks remain
grep -r "sys.path.append\|sys.path.insert" --include="*.py" | grep -v ".pyenv"

# Editable install works
python -c "import config_manager; import logger; import file_discovery; print('OK')"

# Tests pass
pytest -v
```
