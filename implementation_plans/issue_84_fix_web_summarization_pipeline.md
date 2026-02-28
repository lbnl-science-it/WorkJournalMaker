# Issue #84: Fix WebSummarizationService Broken Pipeline

## Problem

`WebSummarizationService._execute_summarization` has two bugs:
1. **Skips LLM analysis** (phase 3 of the 4-phase pipeline) — collapses `List[ProcessedContent]` into a raw string
2. **Calls non-existent methods** on `SummaryGenerator`: `generate_weekly_summary()`, `generate_monthly_summary()`, `generate_custom_summary()` — the real API is `generate_summaries(analysis_results, summary_type, start_date, end_date)`

## Fix: Shared Pipeline Module (DRY)

Extract the CLI's correct 4-phase pipeline logic into pure functions (no `print()`), then have both CLI and web call them.

## Files to Create

| File | Purpose |
|------|---------|
| `summarization_pipeline.py` | 4 pure pipeline functions |
| `tests/test_summarization_pipeline.py` | Unit tests for pipeline module |

## Files to Modify

| File | Changes |
|------|---------|
| `web/services/web_summarizer.py` | Rewrite `_execute_summarization` to call pipeline; remove 3 broken methods |
| `work_journal_summarizer.py` | `_run_*` functions delegate to pipeline, keep `print()` display code |
| `tests/test_web_summarization_service.py` | Rewrite/remove 3 tests that validated broken methods |

## Pipeline Functions (in `summarization_pipeline.py`)

```
discover_files(base_path, start_date, end_date) → FileDiscoveryResult
process_content(file_paths, max_file_size_mb=50) → (List[ProcessedContent], ProcessingStats)
analyze_content(processed_content, config, on_fallback=None) → (List[AnalysisResult], APIStats, UnifiedLLMClient)
generate_summaries(analysis_results, llm_client, summary_type, start_date, end_date) → (List[PeriodSummary], SummaryStats)
```

## TDD Steps

### Step 1: Write failing tests for pipeline module
- `test_summarization_pipeline.py` — tests for all 4 functions
- Mock underlying components (`FileDiscovery`, `ContentProcessor`, `UnifiedLLMClient`, `SummaryGenerator`)
- Confirm tests fail (module doesn't exist)

### Step 2: Implement pipeline module (make tests green)
- Create `summarization_pipeline.py` with the 4 functions
- Each function creates its own component instance, calls the real API, returns results
- No `print()`, no display logic — pure data transformation

### Step 3: Refactor CLI to use shared pipeline
- `_run_file_discovery` → calls `pipeline.discover_files()`, then prints results
- `_run_content_processing` → calls `pipeline.process_content()`, then prints stats
- `_run_llm_analysis` → calls `pipeline.analyze_content()`, then prints entities/stats
- `_run_summary_generation` → calls `pipeline.generate_summaries()`, then prints summaries
- Run existing CLI tests to verify no regressions

### Step 4: Write failing tests for fixed web summarizer
- Rewrite `test_execute_summarization_success` to mock pipeline functions instead of broken methods
- Remove `test_async_content_processing` (method being deleted)
- Remove `test_async_summary_generation` (tested non-existent methods)
- Remove `test_async_output_saving` (method being deleted)
- Add `test_execute_summarization_calls_all_four_phases`
- Confirm tests fail

### Step 5: Fix web summarizer (make tests green)
- Rewrite `_execute_summarization` to call all 4 pipeline phases via `run_in_executor`
- Remove broken methods: `_process_content_async`, `_generate_summary_async`, `_save_output_async`
- Remove unused component instantiation from `__init__` (keep `self.llm_client` — WebSocket check at `summarization.py:457` needs it)
- Use `asyncio.get_running_loop()` instead of deprecated `get_event_loop()`
- Use `functools.partial` for `run_in_executor` calls with multiple args

### Step 6: Run full test suite
- Baseline: 1358 passed, 170 failed, 27 errors (all pre-existing)
- Must not increase failure count

### Step 7: E2E verification with Playwright (MANDATORY)
- Start web server on a test port
- Navigate to the summarization page
- Submit a summarization request
- Verify task creation succeeds (no AttributeError in console)
- Check that the task progresses through all 4 phases (progress updates visible)
- Verify no JavaScript console errors
- Close browser and stop server

### Step 8: Commit

## Key Gotchas

1. **`self.llm_client` must stay** in `WebSummarizationService.__init__` — WebSocket endpoint checks `hasattr(summarization_service, 'llm_client')` at `web/api/summarization.py:457`
2. **`run_in_executor` only takes positional args** — use `functools.partial` for pipeline function calls
3. **`SummaryType.CUSTOM`** maps to `"custom"` string — `SummaryGenerator._group_by_periods` treats non-"weekly" as monthly. Pre-existing behavior, not introduced by this fix.
4. **Mock paths** — CLI tests that mock `FileDiscovery` etc. at `work_journal_summarizer` module level will need mock paths updated to `summarization_pipeline` module level
5. **Entity aggregation** — the CLI's `_run_llm_analysis` also builds `entity_sets` (projects, participants, tasks, themes) for display and `ProcessingMetadata`. This aggregation stays in the CLI's `_run_llm_analysis` wrapper, not in the pipeline function.
