# Cluster F: CLI Cleanup — Implementation Plan

**Source:** `improvements.md` items #4, #5, #11, #18
**Branch:** `improvements/cluster-f-cli-cleanup`
**Depends on:** Cluster A only (independent of B-E chain)

---

## Overview

Four cleanup items targeting CLI pipeline code:

| Step | Item | File | Risk | Scope |
|------|------|------|------|-------|
| 1 | #18 | `file_discovery.py` | Low | Remove ~225 lines of dead migration scaffolding |
| 2 | #11 | `file_discovery.py` | Low | Remove mock-detection logic from production code |
| 3 | #4 | `work_journal_summarizer.py` | Low | Fix hardcoded provider output |
| 4 | #5 | `work_journal_summarizer.py` | Medium | Decompose 519-line `main()` into phase functions |

**Ordering rationale:** Start with the safest, most mechanical deletions (#18, #11)
in `file_discovery.py`, then fix the small provider output bug (#4), and finish
with the largest refactor (#5). Steps 1-2 touch `file_discovery.py`; steps 3-4
touch `work_journal_summarizer.py`. No cross-file dependencies between steps.

---

## Step 1: Remove Migration Scaffolding from file_discovery.py

**Item:** #18 from improvements.md
**Risk:** Low — methods are not called by any production code.

### What to change

Remove these three methods from `FileDiscovery`:
- `compare_discovery_results()` (lines 781-867, ~87 lines)
- `validate_migration_success_criteria()` (lines 869-956, ~88 lines)
- `_log_migration_validation()` (lines 958-1007, ~50 lines)

Total: ~225 lines of dead code.

### Tests to update

Remove the corresponding tests from `tests/test_file_discovery_v2_core_functionality.py`:
- `test_compare_discovery_results_identical` (line 151)
- `test_compare_discovery_results_different` (line 163)
- `test_compare_discovery_results_with_detailed_analysis` (line 188)
- `test_validate_migration_success_criteria` (line 215)
- `test_validate_migration_failure_criteria` (line 243)
- `_create_mock_result` helper (line 270, only used by the above tests)

### Verification

1. Run full file_discovery test suite — all tests pass
2. Grep codebase for removed method names — zero hits outside improvements.md

### Prompt

```text
Remove the migration scaffolding methods from file_discovery.py. These methods
are not called by any production code and exist only as one-time migration
validation tools that have served their purpose.

Remove these methods from the FileDiscovery class:
- compare_discovery_results() (lines 781-867)
- validate_migration_success_criteria() (lines 869-956)
- _log_migration_validation() (lines 958-1007)

Also remove the corresponding tests from
tests/test_file_discovery_v2_core_functionality.py:
- test_compare_discovery_results_identical
- test_compare_discovery_results_different
- test_compare_discovery_results_with_detailed_analysis
- test_validate_migration_success_criteria
- test_validate_migration_failure_criteria
- _create_mock_result helper (only used by the above tests)

After removal, run the full file_discovery test suite to confirm no regressions:
  pytest tests/test_file_discovery*.py -v

Verify with grep that no production code references the removed methods.
```

---

## Step 2: Remove Mock-Detection Logic from file_discovery.py

**Item:** #11 from improvements.md
**Risk:** Low — removing test infrastructure that leaked into production code.

### What to change

In `_construct_missing_file_path()` (lines 702-779), there are three blocks
that check `hasattr(result, '_mock_name')` to detect mock objects:

1. Lines 738-746: First match block
2. Lines 756-764: Closest-match fallback block
3. Lines 769-777: Final fallback block

Each block follows this pattern:
```python
result = directory_path / filename
if hasattr(result, 'name') and not hasattr(result, '_mock_name'):
    return result
else:
    return Path(str(directory_path)) / filename
```

Replace each with simply:
```python
return directory_path / filename
```

The `try/except (TypeError, AttributeError)` around each can also be removed
since `directory_path` is always a `Path` object from the directory scanner.

### TDD approach

1. Write a test for `_construct_missing_file_path` using real `Path` objects
   (not mocks) that validates the method returns correct paths
2. Confirm test passes with current code
3. Simplify the method by removing mock-detection
4. Confirm test still passes

### Verification

1. Run full file_discovery test suite
2. Grep for `_mock_name` in production code — zero hits

### Prompt

```text
Remove mock-detection logic from _construct_missing_file_path() in
file_discovery.py. The method currently has hasattr(result, '_mock_name')
checks at three locations — this is test infrastructure that leaked into
production code.

TDD approach:
1. First, write a test in tests/test_file_discovery_v2_file_extraction.py
   that tests _construct_missing_file_path with real Path objects:
   - Test with a matching week directory (week_start <= date <= week_ending)
   - Test with a closest-match fallback directory
   - Test with only one directory available (final fallback)
   - Test with empty directories list (returns None)

2. Run the test to confirm it passes with the current code.

3. Simplify _construct_missing_file_path by replacing each of the three
   mock-detection blocks:

   BEFORE (repeated 3 times with slight variations):
   ```python
   try:
       result = directory_path / filename
       if hasattr(result, 'name') and not hasattr(result, '_mock_name'):
           return result
       else:
           return Path(str(directory_path)) / filename
   except (TypeError, AttributeError):
       return Path(str(directory_path)) / filename
   ```

   AFTER:
   ```python
   return directory_path / filename
   ```

4. Run the test again to confirm it still passes.
5. Run the full file_discovery test suite: pytest tests/test_file_discovery*.py -v
6. Grep for _mock_name in all non-test .py files to verify zero hits.
```

---

## Step 3: Fix Provider-Specific Output in work_journal_summarizer.py

**Item:** #4 from improvements.md
**Risk:** Low — two lines of print output.

### What to change

Lines 514-515 in `main()`:
```python
print(f"AWS Region: {config.bedrock.region}")
print(f"Model: {config.bedrock.model_id}")
```

Replace with provider-agnostic output using the same pattern already used in
`_perform_dry_run()` (lines 370-374):
```python
llm_client = UnifiedLLMClient(config, on_fallback=fallback_notification)
provider_info = llm_client.get_provider_info()
for key, value in provider_info.items():
    if key not in ("fallback_providers",):
        print(f"{key.replace('_', ' ').title()}: {value}")
```

### TDD approach

1. Create `tests/test_work_journal_summarizer.py`
2. Write a test that verifies provider-agnostic output: mock the
   `UnifiedLLMClient` to return google_genai provider info and confirm
   stdout does NOT contain "AWS Region"
3. Implement the fix
4. Confirm tests pass

### Verification

1. Run the new tests
2. Grep for "AWS Region" in work_journal_summarizer.py — zero hits

### Prompt

```text
Fix the hardcoded provider output in work_journal_summarizer.py. Lines 514-515
always print AWS Region and Bedrock Model regardless of which LLM provider is
active. When using google_genai, this displays misleading information.

TDD approach:
1. Create tests/test_work_journal_summarizer.py with tests that verify
   provider-agnostic output:
   - Test that with a google_genai config, the banner does NOT print
     "AWS Region" or "Model: anthropic..."
   - Test that the banner prints provider info from get_provider_info()
   You will need to mock UnifiedLLMClient and config appropriately since
   we cannot make real API calls in unit tests. Focus on testing that the
   correct provider_info keys are printed, not the LLM behavior itself.

2. Run the test — it should fail because current code hardcodes Bedrock output.

3. Replace lines 514-515 with provider-agnostic output. The dry_run path
   (_perform_dry_run, lines 370-374) already does this correctly — follow
   that pattern:
   ```python
   llm_client = UnifiedLLMClient(config, on_fallback=fallback_notification)
   provider_info = llm_client.get_provider_info()
   for key, value in provider_info.items():
       if key not in ("fallback_providers",):
           print(f"{key.replace('_', ' ').title()}: {value}")
   ```

4. Run the test — it should pass.
5. Run the full test suite to check for regressions.
```

---

## Step 4: Decompose main() into Phase Functions

**Item:** #5 from improvements.md
**Risk:** Medium — largest change; must preserve exact phase ordering and error handling.

### Analysis of current main()

The 519-line `main()` (lines 425-943) contains these logical phases:

| Phase | Lines | Description |
|-------|-------|-------------|
| Args & Config | 442-516 | Parse args, init config, init logger, display banner |
| File Discovery | 521-596 | Discover journal files |
| Content Processing | 597-651 | Process file content |
| LLM Analysis | 653-738 | Analyze content with LLM API |
| Summary Generation | 743-821 | Generate intelligent summaries |
| Output Management | 824-874 | Create markdown output |
| Quality Metrics | 911-928 | Display content quality stats |
| Error Handling | 929-943 | No-files-found + KeyboardInterrupt + catch-all |

### Decomposition strategy

Extract each phase into a standalone function. Each function:
- Takes explicit parameters (no globals)
- Returns its results as a value
- Raises on unrecoverable failure
- Handles its own try/except for recoverable errors

`main()` becomes a thin orchestrator that calls each phase function in sequence.

### Incremental approach (4 sub-steps)

Because this is a large refactor, we break it into sub-steps that each leave
the code in a working state:

#### 4a: Extract file discovery phase
Extract lines 521-596 into `_run_file_discovery()`.

#### 4b: Extract content processing and LLM analysis phases
Extract lines 597-738 into `_run_content_processing()` and `_run_llm_analysis()`.

#### 4c: Extract summary generation and output phases
Extract lines 743-874 into `_run_summary_generation()` and `_run_output_generation()`.

#### 4d: Extract initialization and cleanup
Extract the banner display and quality metrics into helper functions.
Clean up `main()` to be a pure orchestrator.

### TDD approach

Build on the test file created in Step 3. For each sub-step:

1. Write a test for the extracted function in isolation
2. Extract the function
3. Verify the test passes
4. Run the full test suite to verify no regressions

### Prompt

```text
Decompose the 519-line main() function in work_journal_summarizer.py into
focused phase functions. The goal is for main() to become a thin orchestrator
that calls each phase in sequence.

This is a large refactor. Do it incrementally in 4 sub-steps, running tests
after each sub-step.

IMPORTANT: Preserve exact behavior. Do not change logic, error messages, print
output, or error handling semantics. This is a pure structural refactor.

Sub-step 4a — Extract file discovery:
  Extract the file discovery phase into a function:
    def _run_file_discovery(config, args, logger) -> FileDiscoveryResult
  - Takes config, args, logger as parameters
  - Returns FileDiscoveryResult
  - Handles its own try/except, returns empty result on failure
  - Write a test that verifies it returns a FileDiscoveryResult

Sub-step 4b — Extract content processing and LLM analysis:
  Extract into:
    def _run_content_processing(found_files, config) -> Tuple[List[ProcessedContent], ProcessingStats]
  Extract into:
    def _run_llm_analysis(processed_content, config) -> Tuple[List[AnalysisResult], APIStats, dict]
  - The dict return from _run_llm_analysis contains the aggregated entity sets
  - Write tests for each function

Sub-step 4c — Extract summary and output:
  Extract into:
    def _run_summary_generation(analysis_results, llm_client, args) -> Tuple[List[PeriodSummary], SummaryStats]
  Extract into:
    def _run_output_generation(summaries, args, discovery_result, processing_stats, api_stats, summary_stats, entity_sets, config) -> OutputResult
  - Write tests for each function

Sub-step 4d — Clean up main():
  Extract the banner display into:
    def _display_banner(args, config, provider_info)
  Extract quality metrics into:
    def _display_quality_metrics(processed_content)
  Clean up main() to be a linear orchestrator:
    1. Parse args & init config/logger
    2. Handle special modes (save-example-config, dry-run)
    3. _display_banner()
    4. _run_file_discovery()
    5. _run_content_processing()
    6. _run_llm_analysis()
    7. _run_summary_generation()
    8. _run_output_generation()
    9. _display_quality_metrics()

After all sub-steps, main() should be ~50-80 lines of orchestration code.
Run the full test suite after each sub-step.
```

---

## Verification Checklist

After all 4 steps:

- [ ] `pytest tests/test_file_discovery*.py -v` — all pass
- [ ] `pytest tests/test_work_journal_summarizer.py -v` — all pass
- [ ] `pytest -v` — full suite passes
- [ ] `grep -r '_mock_name' *.py` — zero hits in production code
- [ ] `grep -r 'compare_discovery_results\|validate_migration_success' *.py` — zero hits outside improvements.md
- [ ] `grep -r 'AWS Region' work_journal_summarizer.py` — zero hits
- [ ] `main()` is ≤80 lines
- [ ] No behavioral changes to CLI output (except provider-specific lines)
