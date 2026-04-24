# Repo Cleanup Design Spec

**Date:** 2026-04-23
**Branch:** `repo-cleanup` (rebase on `main` after `fix/111-calendar-test-self-contained` merges)
**Goal:** Ship-readiness + developer ergonomics — remove debris, organize files, fix git tracking.
**Scope:** File moves, deletes, and `.gitignore` fixes only. No source code restructuring (flat layout stays for now).

## Prerequisites

- Merge `fix/111-calendar-test-self-contained` (issues #111, #112) into `main`
- Rebase `repo-cleanup` onto updated `main`

## Target Directory Structure

```
WorkJournalMaker/
├── (14 source .py files — unchanged at root)
├── conftest.py
├── pyproject.toml
├── requirements.txt
├── package.json
├── license.txt
├── README.md
├── config.yaml              (gitignored, local only)
├── WorkJournalMaker.spec
│
├── debug_scripts/            (consolidated debug/diagnostic tools)
│   ├── (existing 7 scripts)
│   ├── reset_database_with_fix.py  (moved from root)
│   ├── debug_database_sync.py      (moved from tests/)
│   ├── debug_date_display_issues.py (moved from tests/)
│   ├── debug_date_mapping.py        (moved from tests/)
│   ├── debug_google_genai_connection.py (moved from tests/)
│   ├── debug_journal_access.py      (moved from tests/)
│   ├── debug_settings_error.py      (moved from tests/)
│   ├── debug_timezone_issue.py      (moved from tests/)
│   ├── geminitest.py                (moved from tests/)
│   └── bedrock_model_checker.py     (moved from tests/)
│
├── docs/
│   ├── llm_providers.md
│   ├── superpowers/specs/
│   └── archive/
│       ├── completion_summaries/    (moved from root)
│       ├── implementation_plans/    (moved from root)
│       ├── failure_images/          (moved from root)
│       ├── improvement_metaplan.md  (moved from root)
│       ├── improvements.md          (moved from root)
│       ├── plan.md                  (moved from root)
│       ├── todo.md                  (moved from root)
│       ├── build_deployment_instructions.md  (moved+renamed from root)
│       └── local_build_instructions.md       (moved+renamed, emoji removed)
│
├── packaging/                (all build/desktop/installer work)
│   ├── desktop/              (moved from root)
│   ├── build_system/         (moved from root)
│   └── scripts/              (moved from root)
│
├── tests/                    (actual tests only)
│   ├── integration/
│   ├── conftest.py
│   └── test_*.py files
│
└── web/                      (unchanged internally)
```

## Actions

### Phase 1: Delete Debris (no code changes)

| # | Action | Notes |
|---|--------|-------|
| 1 | Delete `:memory:` | Stale duplicate DB (0 journal entries, just defaults). Real DB is `web/journal_index.db` |
| 2 | Delete `.coverage` | Stale coverage from Aug 2025 |
| 3 | Delete `.src/` | Empty directory |
| 4 | Delete `custom/` | Empty directory (contains empty `database/` subdir) |
| 5 | Delete `web/web/` | Stale duplicate DB + empty dirs |
| 6 | Delete `web/build/` | Empty build artifact directory |
| 7 | Delete `web/dist/` | Empty dist artifact directory |

### Phase 2: Remove Tracked-but-Gitignored Files from Git

These files are in `.gitignore` but were committed before the rules were added. Remove from tracking but keep locally where needed.

```bash
git rm -r --cached build/
git rm -r --cached dist/
git rm -r --cached __pycache__/
git rm -r --cached .pytest_cache/
git rm -r --cached workjournalmaker.egg-info/
git rm --cached .DS_Store
git rm --cached package-lock.json
git rm --cached .coverage
```

**Expected repo size reduction:** ~189MB (build/ + dist/)

### Phase 3: Organize Documentation

Move accumulated AI session artifacts and planning docs to `docs/archive/`:

```bash
mkdir -p docs/archive

git mv completion_summaries/ docs/archive/completion_summaries/
git mv implementation_plans/ docs/archive/implementation_plans/
git mv failure_images/ docs/archive/failure_images/

git mv improvement_metaplan.md docs/archive/
git mv improvements.md docs/archive/
git mv plan.md docs/archive/
git mv todo.md docs/archive/

# Rename to remove emoji and normalize
git mv "⏺ Local Build Instructions.md" docs/archive/local_build_instructions.md
git mv BUILD_DEPLOYMENT_INSTRUCTIONS.md docs/archive/build_deployment_instructions.md
```

### Phase 4: Consolidate Build/Packaging

Move build infrastructure into a single `packaging/` directory:

```bash
mkdir -p packaging

git mv desktop/ packaging/desktop/
git mv build_system/ packaging/build_system/
git mv scripts/ packaging/scripts/
```

### Phase 5: Clean `tests/` Directory

Move non-test scripts to `debug_scripts/`. Delete stale test artifacts.

**Move to `debug_scripts/`:**
- `tests/debug_database_sync.py`
- `tests/debug_date_display_issues.py`
- `tests/debug_date_mapping.py`
- `tests/debug_google_genai_connection.py`
- `tests/debug_journal_access.py`
- `tests/debug_settings_error.py`
- `tests/debug_timezone_issue.py`
- `tests/geminitest.py`
- `tests/bedrock_model_checker.py`

**Move to `debug_scripts/`:**
- `reset_database_with_fix.py` (from root)
- `tests/simple_sync_validation.py`

**Delete:**
- `tests/comprehensive_test_report.json` (stale artifact)
- `tests/pytest_calendar.ini` (unused; pytest handles test selection natively)
- `tests/run_calendar_tests.py` (runner script, not a test)
- `tests/run_comprehensive_tests.py` (runner script, not a test)
- `tests/run_summarization_tests.py` (runner script, not a test)

### Phase 6: Update `.gitignore`

**Add rules:**
```
# Packaging build outputs
packaging/desktop/__pycache__/
packaging/build_system/__pycache__/
packaging/scripts/__pycache__/

# Prevent stray nested web dir
web/web/
web/build/
web/dist/
```

**Update rules:**
- `failure_images/` → `docs/archive/failure_images/` (or remove since it's now tracked in archive)

**Verify existing rules still cover:**
- `build/`, `dist/`, `__pycache__/`, `*.db`, `.DS_Store`, `config.yaml`, `logs/`, `node_modules/`

### Phase 7: Relocate Production Database (Issue #114)

**This phase modifies code and requires testing.**

- Move default DB location from `web/journal_index.db` to `~/.workjournal/journal_index.db` (macOS/Linux) or `%APPDATA%/WorkJournal/journal_index.db` (Windows)
- Simplify the fallback cascade in `web/database.py`
- Update `_get_default_database_path()` to use platform-appropriate data directory as primary location (not just for frozen executables)
- Add first-run migration: if DB exists at old location but not new, copy it
- Update tests that reference `web/journal_index.db` path

**References:** Issue #114 (lbnl-science-it/WorkJournalMaker#114)

## Execution Order

1. Phases 1-6 first (file moves/deletes only, no code changes)
2. Phase 7 separately (code changes, requires testing)
3. Each phase should be a separate commit for easy review/revert

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Moved files break imports | Low | Phases 1-6 only move non-source files |
| Tests reference moved debug scripts | Low | Debug scripts aren't imported by tests |
| Phase 7 DB migration breaks existing installs | Medium | First-run copy from old→new location |
| Git history becomes harder to trace | Low | `git log --follow` tracks renames |

## Out of Scope

- Moving source `.py` files into a `src/workjournalmaker/` package (Phase 2 effort)
- Restructuring the flat `tests/` directory into subdirectories
- Any functional code changes (except Phase 7)
