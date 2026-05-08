# Root Directory Stale File Cleanup

**Date:** 2026-05-08
**Branch:** refactor/organize-root-scripts
**Scope:** Phase 1 of a two-phase cleanup. Remove stale files, empty
directories, and orphaned scripts from the repository root.

## Context

The root directory accumulated clutter over ~2 years of agentic development:
empty placeholder directories, historical AI session logs, accidental file
saves, and one-off scripts. None of these items are imported by application
code or referenced by the build system. All are preserved in git history.

## Phase 1: Stale File Removal (This Spec)

### Files to delete

| Item | Reason |
|------|--------|
| `:memory:` | Accidental SQLite file from `sqlite:///:memory:` URL mishap |
| `⏺ Local Build Instructions.md` | Accidentally saved from Claude output |
| `reset_database_with_fix.py` | One-off maintenance script, not imported by anything |

### Directories to delete (with all contents)

| Item | Contents | Reason |
|------|----------|--------|
| `completion_summaries/` | 30 AI session logs | Historical, no code dependency |
| `implementation_plans/` | 18 planning docs | Superseded by code and `docs/superpowers/specs/` |
| `data/` | Empty | Unused placeholder |
| `custom/` | Empty subdirectory | Unused placeholder |
| `.src/` | Empty | Unknown purpose, unused |
| `failure_images/` | 7 test screenshots | Accidentally committed, already gitignored |

### .gitignore addition

`failure_images/` is already listed in `.gitignore` but files were committed
before the ignore rule was added. No new ignore rules needed — the existing
rule prevents recurrence once the tracked files are removed.

### Items explicitly kept

- All 15 core `.py` modules in root (Phase 2 scope)
- `debug_scripts/` (active dev tools, referenced in `pyproject.toml`)
- `logs/` (empty but valid runtime directory)
- All config and project files (`pyproject.toml`, `README.md`, `todo.md`, etc.)
- `web/`, `desktop/`, `tests/`, `scripts/`, `build_system/`, `docs/`

### Verification

Run `pytest` after deletions to confirm no tests depend on deleted items.
All deleted items are unimported, so this is a confidence check.

### todo.md update

Add Phase 2 (package restructure) as a future item, gated on completion of
`feature/87-authentication`.

## Phase 2: Package Restructure (Future)

Move the 15 root-level core modules into a `workjournalmaker/` package with
sub-packages (`llm/`, `summarization/`, etc.). This touches every import in
the project and must not run concurrently with active feature branches.

**Trigger:** After `feature/87-authentication` merges to main.

Phase 2 will get its own design spec when the time comes.
