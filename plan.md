# Cluster B: Import / Type Cleanup — Implementation Plan

**Source:** `improvements.md` items #1, #3, #7, #10
**Branch:** `improvements/code-review`
**Depends on:** Cluster A (complete)

## Problem Summary

The LLM client layer has a type identity split. `llm_data_structures.py` is the
canonical home for `AnalysisResult` and `APIStats`, but `llm_client.py` carries
its own copies. `summary_generator.py` imports from `llm_client.py`, getting the
wrong `AnalysisResult` class. The entire `llm_client.py` module (413 lines) is
dead code — `UnifiedLLMClient` delegates to `BedrockClient`/`GoogleGenAIClient`,
never to `LLMClient`. Additionally, `ProcessingConfig.rate_limit_delay` is
unused — only `BedrockConfig.rate_limit_delay` is used in production.

## Design Decision

**LLM client interface: Protocol (structural subtyping)**

A `typing.Protocol` class will be defined in `llm_data_structures.py` specifying
the methods that all LLM clients must implement: `analyze_content()`,
`get_stats()`, `reset_stats()`, `test_connection()`, `get_provider_info()`.
This formalizes the duck-typed contract without requiring inheritance changes to
existing concrete classes.

## Affected Files

### Production code
| File | Change |
|------|--------|
| `llm_data_structures.py` | Add `LLMClientProtocol` |
| `summary_generator.py` | Fix imports, use Protocol for type hint |
| `llm_client.py` | Delete entirely |
| `config_manager.py` | Remove `rate_limit_delay` from `ProcessingConfig` |

### Test code
| File | Change |
|------|--------|
| `tests/test_llm_data_structures.py` | New — test Protocol conformance |
| `tests/test_llm_client.py` | Delete (tests dead code) |
| `tests/test_summary_generator.py` | Update imports |
| `tests/test_database_config.py` | Remove `rate_limit_delay` assertion |

### Files that import from `llm_client.py` (verified via grep)
- `summary_generator.py:22` — `from llm_client import LLMClient, AnalysisResult`
- `tests/test_llm_client.py:19` — `from llm_client import LLMClient, AnalysisResult, APIStats`
- `tests/test_summary_generator.py:23` — `from llm_client import LLMClient, AnalysisResult`
- `improvements.md` / `implementation_plans/` — documentation only (no code change needed)

## Implementation Steps

Steps are ordered so the test suite stays green after each commit.

---

### Step 1: Add LLMClientProtocol to llm_data_structures.py (TDD)

**Scope:** Add a `typing.Protocol` class that formalizes the LLM client interface.

**Why first:** Additive change — nothing breaks. Creates the type that
subsequent steps depend on.

**TDD approach:**
1. Write tests verifying the Protocol exists and that a conforming class
   passes `isinstance()` with `runtime_checkable`.
2. Implement the Protocol.
3. Verify all tests pass.

**Files touched:**
- `llm_data_structures.py` (add Protocol)
- `tests/test_llm_data_structures.py` (new test file)

```text
PROMPT:

Context: We are working on the WorkJournalMaker project on branch
`improvements/code-review`. The file `llm_data_structures.py` already defines
`AnalysisResult` and `APIStats` dataclasses. Three concrete LLM client classes
exist: `BedrockClient`, `GoogleGenAIClient`, and `UnifiedLLMClient`. All share
the same duck-typed interface:

- analyze_content(content: str, file_path: Path) -> AnalysisResult
- get_stats() -> APIStats
- reset_stats() -> None
- test_connection() -> bool
- get_provider_info() -> Dict[str, Any]

Task (TDD):

1. First, create `tests/test_llm_data_structures.py` with tests that:
   - Verify `LLMClientProtocol` is defined and is `runtime_checkable`
   - Verify that a minimal conforming class passes `isinstance()` check
   - Verify that a non-conforming class fails `isinstance()` check
   - Verify `AnalysisResult` and `APIStats` still work correctly

2. Run the tests — they should FAIL because `LLMClientProtocol` doesn't
   exist yet.

3. Add `LLMClientProtocol` to `llm_data_structures.py` as a
   `typing.Protocol` with `@runtime_checkable`. The Protocol should
   specify the 5 methods listed above with correct type hints.

4. Run the tests — they should PASS.

5. Commit with a descriptive message.
```

---

### Step 2: Fix summary_generator.py imports and type hint (TDD)

**Scope:** Change `summary_generator.py` to import from `llm_data_structures`
and type-hint against `LLMClientProtocol`.

**Why second:** Eliminates the wrong import before we delete the source file.

**TDD approach:**
1. Update test imports first, then fix production imports.
2. Verify tests pass after each change.

**Files touched:**
- `summary_generator.py` (fix imports + type hint)
- `tests/test_summary_generator.py` (fix imports + mock spec)

```text
PROMPT:

Context: We just added `LLMClientProtocol` to `llm_data_structures.py`.
`summary_generator.py` currently has `from llm_client import LLMClient,
AnalysisResult` on line 22 and uses `LLMClient` as the type hint for its
constructor parameter. `tests/test_summary_generator.py` also imports from
`llm_client`.

Task (TDD):

1. Update `tests/test_summary_generator.py`:
   - Change `from llm_client import LLMClient, AnalysisResult` to
     `from llm_data_structures import AnalysisResult, LLMClientProtocol`
   - Update the `mock_llm_client` fixture to use
     `MagicMock(spec=LLMClientProtocol)` instead of `MagicMock(spec=LLMClient)`
   - Remove the `@patch.object(LLMClient, 'analyze_content')` decorator on
     `test_summary_generation` — the mock is already set up via the fixture
   - Remove the `sys.path.insert` hack on line 20 if present

2. Run the tests — they should FAIL because `summary_generator.py` still
   imports `LLMClient` from `llm_client`.

3. Fix `summary_generator.py`:
   - Change `from llm_client import LLMClient, AnalysisResult` to
     `from llm_data_structures import AnalysisResult, LLMClientProtocol`
   - Change the constructor signature from `llm_client: LLMClient` to
     `llm_client: LLMClientProtocol`

4. Run all tests — they should PASS.

5. Commit with a descriptive message.
```

---

### Step 3: Remove dead llm_client.py and its tests

**Scope:** Delete `llm_client.py` and `tests/test_llm_client.py`.

**Why third:** Now that nothing imports from `llm_client.py`, it can be safely
removed.

**Verification approach:**
1. Grep to confirm no production code imports from `llm_client`.
2. Delete files.
3. Run full test suite.

**Files touched:**
- `llm_client.py` (delete)
- `tests/test_llm_client.py` (delete)

```text
PROMPT:

Context: `summary_generator.py` and its tests no longer import from
`llm_client.py`. The `UnifiedLLMClient` delegates to `BedrockClient` and
`GoogleGenAIClient`, never to `LLMClient`. The module is dead code.

Task:

1. Run `grep -r "from llm_client import\|import llm_client" --include="*.py"`
   to confirm no production or test code imports from `llm_client` (ignore
   documentation files like `.md`).

2. Delete `llm_client.py`.

3. Delete `tests/test_llm_client.py` (this test file tested the dead module).

4. Run the full test suite (`pytest -v`) to confirm nothing breaks.

5. Commit with a descriptive message.
```

---

### Step 4: Remove duplicate rate_limit_delay from ProcessingConfig (TDD)

**Scope:** Remove the unused `rate_limit_delay` field from `ProcessingConfig`
in `config_manager.py`.

**Why last:** Independent cleanup with the smallest blast radius.

**TDD approach:**
1. Update test assertion first.
2. Remove the field and its references.
3. Run full test suite.

**Files touched:**
- `config_manager.py` (remove field + references)
- `tests/test_database_config.py` (remove assertion)

```text
PROMPT:

Context: `ProcessingConfig` in `config_manager.py` has a `rate_limit_delay`
field (line 101, default 1.0). `BedrockConfig` also has `rate_limit_delay`
(line 77). Only `BedrockConfig.rate_limit_delay` is used in production code
(in `bedrock_client.py:237`). `ProcessingConfig.rate_limit_delay` is never
read by any production code.

Task (TDD):

1. Update `tests/test_database_config.py`:
   - In `test_default_processing_config_unchanged`, remove the line
     `assert config.rate_limit_delay == 1.0`

2. Run the test — it should still PASS (the field still exists).

3. In `config_manager.py`:
   - Remove `rate_limit_delay: float = 1.0` from `ProcessingConfig` (line 101)
   - In `_parse_processing_config()`, remove the line that reads
     `rate_limit_delay` from the processing dict (~line 313)
   - In `_get_default_config()`, remove `'rate_limit_delay': 1.0` from the
     processing section (~line 487)

4. Run the full test suite (`pytest -v`) to confirm nothing breaks.

5. Commit with a descriptive message.
```

---

## Risk Assessment

| Step | Risk | Mitigation |
|------|------|------------|
| 1 - Add Protocol | None (additive) | Tests verify conformance |
| 2 - Fix imports | Low | Tests verify import works |
| 3 - Delete dead code | Low | Grep verification first |
| 4 - Remove config field | Low | Grep confirms unused |

## Verification

After all steps, run:
```bash
pytest -v
grep -r "from llm_client import" --include="*.py"  # Should find nothing
grep -r "ProcessingConfig.*rate_limit" --include="*.py"  # Should find nothing
```
