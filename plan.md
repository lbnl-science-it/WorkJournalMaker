# Cluster C: LLM Client Consolidation — Implementation Plan

**Source:** `improvements.md` items #2, #6, #8, #9
**Branch:** `improvements/cluster-c-llm-consolidation`
**Risk level:** High — core API integration layer

## Context

The two LLM client modules (`bedrock_client.py` and `google_genai_client.py`)
share ~6 copy-pasted methods. `UnifiedLLMClient` currently delegates to a single
provider with no fallback. CBORG (an OpenAI-compatible API at `cborg.lbl.gov`)
is specified as a tertiary backup but not yet implemented.

### Design Decisions (confirmed by User)

1. **Fallback order:** Google GenAI → AWS Bedrock → CBORG
2. **Fallback UX:** User-visible notification on every provider transition (no silent retry)
3. **CBORG role:** Tertiary/deep-backup — only used when both GCP and AWS fail

### Current Architecture

```
UnifiedLLMClient  ──delegates-to──►  BedrockClient  |  GoogleGenAIClient
                                          │                    │
                                    (each has own copy of shared logic)
```

### Target Architecture

```
                       BaseLLMClient (ABC)
                     ┌──────┼──────────┐
                     ▼      ▼          ▼
              BedrockClient  GoogleGenAIClient  CBORGClient
                     ▲      ▲          ▲
                     └──────┼──────────┘
                    UnifiedLLMClient (with fallback chain)
```

## Steps

### Step 1: Extract `BaseLLMClient` with shared logic

**Goal:** Create `base_llm_client.py` containing an abstract base class that owns
all duplicated methods. Both `BedrockClient` and `GoogleGenAIClient` inherit from
it. Zero behavioral change — pure refactor with tests proving equivalence.

**Shared code to extract:**
- `ANALYSIS_PROMPT` class constant
- `_create_analysis_prompt()` — content truncation + prompt formatting
- `_extract_json_from_text()` — markdown/raw JSON extraction
- `_deduplicate_entities()` — entity normalization and dedup
- `get_stats()` / `reset_stats()` — stats management
- Stats bookkeeping in `analyze_content()` (timing, success/failure counting)

**Abstract methods (provider-specific):**
- `_make_api_call(prompt) -> str` — raw API call returning response text
- `_parse_raw_response(response) -> str` — extract text from provider response format
- `test_connection() -> bool` — provider-specific connectivity check
- `get_provider_info() -> Dict` — provider metadata

**TDD approach:**
1. Write tests for `BaseLLMClient` shared methods in isolation (using a concrete test subclass)
2. Write tests verifying `BedrockClient` and `GoogleGenAIClient` still pass their existing test suites
3. Refactor to extract base class
4. Verify all tests pass

```text
Implement Step 1 of the Cluster C plan (LLM Client Consolidation).

Create `base_llm_client.py` containing a `BaseLLMClient` abstract base class.
Extract the following shared methods from `bedrock_client.py` and
`google_genai_client.py` into the base class:

- `ANALYSIS_PROMPT` (class constant — identical in both clients)
- `_create_analysis_prompt(content)` — truncates content at 8000 chars, formats with ANALYSIS_PROMPT
- `_extract_json_from_text(text)` — extracts JSON from markdown code blocks or raw text
- `_deduplicate_entities(entities)` — normalizes and deduplicates entity lists
- `get_stats()` / `reset_stats()` — returns/resets the `self.stats` APIStats instance
- The stats bookkeeping logic from `analyze_content()` (timing, success/failure counting)

The base class should define these abstract methods for subclasses:
- `_make_api_call(prompt: str) -> str` — provider-specific API call returning raw response text
- `_parse_raw_response(raw_response) -> str` — extract text content from provider response format
- `test_connection() -> bool`
- `get_provider_info() -> Dict[str, Any]`

The base class `analyze_content()` method should implement the shared flow:
1. Increment total_calls, record start_time
2. Call `_create_analysis_prompt(content)`
3. Call `_make_api_call(prompt)` (abstract — subclass provides)
4. Call `_extract_json_from_text()` + `json.loads()` + field validation
5. Call `_deduplicate_entities()`
6. Build and return `AnalysisResult`
7. On failure: increment failed_calls, return empty AnalysisResult

TDD: Write tests FIRST for `BaseLLMClient` shared methods using a minimal
concrete test subclass (e.g., `_TestClient(BaseLLMClient)` that implements
the abstract methods with simple stubs). Then refactor `BedrockClient` and
`GoogleGenAIClient` to inherit from `BaseLLMClient`, removing their duplicated
code. Run ALL existing tests to verify no regressions.

IMPORTANT: `BedrockClient._parse_bedrock_response()` extracts text from Bedrock's
`response['content'][0]['text']` format, then calls `_extract_json_from_text()`.
`GoogleGenAIClient._parse_response()` calls `_extract_json_from_text()` directly
on the already-extracted text. The base class should handle the shared part
(JSON extraction + field validation), while each subclass handles its own raw
response format.

Add ABOUTME comments to `base_llm_client.py`. The file starts with:
# ABOUTME: Abstract base class for LLM provider clients.
# ABOUTME: Owns shared prompt templates, JSON parsing, entity dedup, and stats tracking.

Use the pyenv WorkJournal virtual environment for running tests.
```

---

### Step 2: Add `CBORGConfig` and CBORG client

**Goal:** Add configuration support for CBORG and implement a `CBORGClient` that
inherits from `BaseLLMClient`. CBORG is an OpenAI-compatible API at
`https://cborg.lbl.gov`. The client should be functional but is the lowest
priority provider (tertiary fallback).

**Details:**
- Add `CBORGConfig` dataclass to `config_manager.py` with endpoint URL, API key
  env var name, model name, and retry settings
- Add `cborg` field to `AppConfig`
- Add `cborg` to `LLMConfig.provider` options
- Create `cborg_client.py` inheriting from `BaseLLMClient`
- CBORG uses the OpenAI-compatible chat completions API format

**TDD approach:**
1. Write tests for `CBORGClient` covering initialization, API call format,
   response parsing, and error handling
2. Implement the client
3. Verify all tests pass

```text
Implement Step 2 of the Cluster C plan.

Create a CBORG LLM client that inherits from `BaseLLMClient` (created in Step 1).
CBORG is an OpenAI-compatible API at `https://cborg.lbl.gov`.

1. Add `CBORGConfig` to `config_manager.py`:
   - `endpoint: str = "https://cborg.lbl.gov/v1"` (OpenAI-compatible base URL)
   - `api_key_env: str = "CBORG_API_KEY"` (env var name for the API key)
   - `model: str = "lbl/cborg-chat:latest"` (default model)
   - `max_retries: int = 3`
   - `rate_limit_delay: float = 1.0`
   - `timeout: int = 30`

2. Add `cborg: CBORGConfig = field(default_factory=CBORGConfig)` to `AppConfig`

3. Update `LLMConfig` comment to mention "cborg" as an option

4. Create `cborg_client.py` inheriting from `BaseLLMClient`:
   - Uses the `openai` Python package (OpenAI-compatible API)
   - `_make_api_call()` sends chat completion request to CBORG endpoint
   - `_parse_raw_response()` extracts text from OpenAI chat completion format
   - `test_connection()` sends a simple test prompt
   - `get_provider_info()` returns provider, endpoint, model
   - Handle the `openai` import with try/except like `google_genai_client.py`
     handles the `google.genai` import

5. Add ABOUTME comments to `cborg_client.py`:
   # ABOUTME: LLM client for the CBORG service (OpenAI-compatible API at cborg.lbl.gov).
   # ABOUTME: Tertiary fallback provider behind Google GenAI and AWS Bedrock.

TDD: Write tests first in `tests/test_cborg_client.py`. Test initialization,
API call formatting, response parsing, error handling, retry logic, and
stats tracking. Mock the `openai` client — do NOT make real API calls.

Use the pyenv WorkJournal virtual environment for running tests.
```

---

### Step 3: Add provider fallback to `UnifiedLLMClient`

**Goal:** Implement ordered provider fallback in `UnifiedLLMClient`. When the
active provider fails, try the next one in the chain. Notify the user on every
transition.

**Fallback chain:** Google GenAI → Bedrock → CBORG

**Details:**
- `UnifiedLLMClient.__init__` builds an ordered list of provider configs
- On `analyze_content()` failure, catch the exception, log a user-visible warning,
  and retry with the next provider in the chain
- Track which provider is currently active
- `get_provider_info()` reports the active provider and available fallbacks
- The fallback notification callback is injectable (defaults to `logging.warning`)
  so the CLI and web app can present it differently

**TDD approach:**
1. Write tests for fallback chain behavior — primary succeeds, primary fails and
   secondary succeeds, all providers fail, notification callback is called
2. Implement fallback logic
3. Verify all existing `test_unified_llm_client.py` tests still pass

```text
Implement Step 3 of the Cluster C plan.

Add provider fallback logic to `UnifiedLLMClient`. The fallback order is:
Google GenAI (primary) → AWS Bedrock (secondary) → CBORG (tertiary).

Key requirements:
- Fallback must NOTIFY the user when switching providers — no silent retry
- The notification mechanism should be an injectable callback (default:
  `logging.warning`) so CLI and web can present it differently
- `analyze_content()` tries the active provider first; on failure, logs the
  error, calls the notification callback with a clear message like
  "Provider 'google_genai' failed: <error>. Falling back to 'bedrock'.",
  then retries with the next provider
- If all providers fail, raise the last exception (don't swallow errors)
- Track which provider is currently active via `self.active_provider_name`
- `get_provider_info()` reports active provider AND lists available fallbacks
- `test_connection()` tests the active provider; if it fails, try fallbacks
- Provider initialization is lazy — don't create fallback clients until needed
  (avoid failing at startup if a fallback provider's credentials aren't configured)

Config changes:
- Add `fallback_providers: List[str]` to `LLMConfig` (default: empty list)
- The full fallback chain is `[config.llm.provider] + config.llm.fallback_providers`
- Example config: `provider: "google_genai"`, `fallback_providers: ["bedrock", "cborg"]`

Update `UnifiedLLMClient`:
- Accept an optional `on_fallback: Callable[[str], None]` parameter
- Build the provider chain from config
- Add `_create_client_for_provider(provider_name)` that creates the right client
- Add `_try_with_fallback(operation, *args)` that implements the retry chain

TDD: Write tests FIRST in the existing `tests/test_unified_llm_client.py`.
Add a new test class `TestUnifiedLLMClientFallback` covering:
- Primary provider succeeds (no fallback triggered)
- Primary fails, secondary succeeds (notification callback called)
- Primary and secondary fail, tertiary succeeds
- All providers fail (last exception raised)
- Notification callback receives correct messages
- Lazy initialization (fallback client not created until needed)
- `get_provider_info()` reports fallback chain
- Provider chain respects config order

Run ALL existing tests to verify no regressions.

Use the pyenv WorkJournal virtual environment for running tests.
```

---

### Step 4: Wire fallback into CLI and verify end-to-end

**Goal:** Connect the fallback configuration to the CLI entry point and ensure
the full pipeline works with the new fallback behavior. Update config examples.
Add integration-level tests.

**Details:**
- Update `work_journal_summarizer.py` to pass `on_fallback` callback that prints
  to stdout (so the user sees fallback notifications in the terminal)
- Update `config.yaml` example to show `fallback_providers` field
- Add `ConfigManager` support for loading `fallback_providers` and `cborg` config
  from YAML
- Add integration tests that verify the full config → UnifiedLLMClient → fallback
  pipeline works

```text
Implement Step 4 of the Cluster C plan.

Wire the fallback system into the CLI application and configuration pipeline.

1. Update `work_journal_summarizer.py`:
   - When creating `UnifiedLLMClient`, pass an `on_fallback` callback that
     prints a user-visible message to stdout (e.g., using `print()`)
   - The message should be clear: "⚠ Provider 'google_genai' failed. Switching to 'bedrock'."

2. Update `config_manager.py`:
   - Ensure `ConfigManager._load_from_yaml()` correctly deserializes
     `fallback_providers` list in the `llm` section
   - Ensure `cborg` config section is loaded into `AppConfig.cborg`

3. Update default config / documentation:
   - Add example `fallback_providers` and `cborg` sections to config examples
     in the codebase (if any config templates exist)

4. Add integration-level tests:
   - Test that `ConfigManager` correctly loads a config with fallback_providers
   - Test that the full pipeline (config → UnifiedLLMClient → fallback) works
     with mocked providers
   - Test the CLI callback prints the expected output

TDD: Write tests first. Verify all existing tests still pass.

Use the pyenv WorkJournal virtual environment for running tests.
```

---

## Dependency Graph

```
Step 1 (BaseLLMClient extraction)
  │
  ├──► Step 2 (CBORG client)
  │       │
  └───┬───┘
      ▼
  Step 3 (Fallback logic in UnifiedLLMClient)
      │
      ▼
  Step 4 (Wire into CLI + integration tests)
```

## Risk Mitigation

- **TDD throughout**: Every step starts with tests before implementation
- **Incremental refactoring**: Step 1 is a pure refactor — no behavioral change
- **Lazy initialization**: Fallback providers aren't created at startup, avoiding
  credential failures for unconfigured providers
- **Existing test suites**: All existing tests must pass after every step
- **Injectable notifications**: The fallback callback is decoupled from presentation
