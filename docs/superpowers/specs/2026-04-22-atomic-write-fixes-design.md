# Design: Fix Atomic Write & Test Infrastructure Vulnerabilities

**Date:** 2026-04-22
**Branch:** fix/test-data-corruption
**Scope:** 8 issues (5 production, 3 test infrastructure) identified during senior code review

## Context

The fix/test-data-corruption branch introduced atomic write-then-rename in
`entry_manager.py` and test isolation via `isolated_app_client`. A code review
identified 8 issues in this work — race conditions, cross-platform bugs, and
test gaps. This spec covers targeted fixes using Approach A (minimal inline
changes, no new abstractions).

The user depends on this software daily. These fixes must be safe, non-breaking,
and mergeable quickly. A larger security review will follow separately.

## Issues Addressed

| ID | Severity | File | Description |
|----|----------|------|-------------|
| M1 | Medium | entry_manager.py:201 | Concurrent writes share deterministic `.tmp` path — data corruption risk |
| M2 | Medium | entry_manager.py:207-208 | TOCTOU race: `exists()` then `unlink()` in cleanup |
| M3 | Medium | entry_manager.py:205 | `os.rename` fails on Windows when destination exists |
| L1 | Low | entry_manager.py:205 | Synchronous `os.rename` blocks async event loop |
| L2 | Low | test_isolation_sentinel.py:38-69 | Sentinel test passes vacuously in CI (no real worklogs dir) |
| L3 | Low | conftest.py:22-48 | Singleton mutation not safe for parallel test execution |
| L4 | Low | test_atomic_write.py:6-7 | Unused imports (`asyncio`, `Path`) |
| P1 | Pre-existing | entry_manager.py:478-480 | `delete_entry` skips `_ensure_file_discovery_initialized()` |

## Production Code Changes

### `web/services/entry_manager.py`

#### `save_entry_content` — atomic write block (lines 198-209)

Replace the current atomic write implementation with:

```python
import tempfile

fd, tmp_name = tempfile.mkstemp(dir=file_path.parent, suffix='.tmp')
tmp_file = Path(tmp_name)
try:
    os.close(fd)
    async with aiofiles.open(tmp_file, 'w', encoding='utf-8') as file:
        await file.write(content)
    await asyncio.to_thread(os.replace, tmp_file, file_path)
except Exception:
    tmp_file.unlink(missing_ok=True)
    raise
```

Changes and rationale:
- **`tempfile.mkstemp`**: Each write gets a unique temp file, eliminating the
  concurrent-write race where two requests corrupt each other's `.tmp` data (M1).
- **`os.replace`** instead of `os.rename`: Atomically replaces the destination on
  both POSIX and Windows (M3). Same kernel syscall on POSIX.
- **`asyncio.to_thread`**: Wraps the blocking `os.replace` call so it doesn't
  block the event loop (L1).
- **`unlink(missing_ok=True)`**: Eliminates the TOCTOU race between `exists()`
  and `unlink()` (M2). Available since Python 3.8.

The existing comment about atomicity is updated to reflect `os.replace`.

#### `delete_entry` — add initialization guard (line ~478)

Add `await self._ensure_file_discovery_initialized()` before the call to
`_construct_file_path_async()`. This matches the pattern already used by
`get_entry_content` and `save_entry_content` (P1).

#### Import changes

Add `import tempfile` to the module imports. `os` and `asyncio` are already
imported.

## Test Changes

### `tests/test_atomic_write.py`

- **Remove unused imports** (L4): `asyncio` and `Path` are not referenced.
- **Update `test_write_uses_atomic_rename`**: Patch `os.replace` instead of
  `os.rename` in the tracking wrapper, since the production code now calls
  `os.replace` via `asyncio.to_thread`.
- **Add `test_concurrent_writes_use_unique_tmp_files`**: Two rapid sequential
  POSTs for the same date, then assert no `.tmp` files remain and the final
  content is from one of the two writes (not corrupted). Validates M1.

### `tests/test_isolation_sentinel.py`

- **Add `pytest.mark.skipif` to `test_post_entry_does_not_touch_real_worklogs`**
  (L2): Skip when `~/Desktop/worklogs/` month directory doesn't exist, so the
  test doesn't silently pass in CI without exercising its assertions.

### `tests/conftest.py`

- **Add comment** (L3): Document that the `isolated_app_client` fixture mutates
  a module-level singleton and is not compatible with `pytest-xdist`.

### `tests/test_isolation_sentinel.py` (new test for P1)

- **Add `test_delete_entry_without_prior_read_or_write`**: Calls DELETE on a
  fresh `isolated_app_client` as the very first operation (no prior GET or POST).
  Asserts the response does not return a 500 error. Validates that `delete_entry`
  properly initializes `file_discovery` before use. This file already tests
  entry_manager operations via `isolated_app_client`, making it the natural home.

## Testing Strategy

TDD cycle per the project's rules:

1. Update `test_write_uses_atomic_rename` to expect `os.replace` — run, confirm failure
2. Implement `save_entry_content` changes — run, confirm pass
3. Write `test_concurrent_writes_use_unique_tmp_files` — run, confirm pass
4. Write `test_delete_entry_without_prior_read_or_write` — run, confirm failure
5. Add `_ensure_file_discovery_initialized()` to `delete_entry` — run, confirm pass
6. Apply test infrastructure fixes (L2, L3, L4)
7. Run full test suite to confirm no regressions

## Out of Scope

- Extracting a reusable `atomic_write` helper (YAGNI — one write path)
- Third-party library dependencies (`atomicwrites`, etc.)
- Database isolation for test fixtures (separate concern)
- Broader security review fixes (planned as follow-up work)
- Backup/`.bak` file mechanism (separate feature)
