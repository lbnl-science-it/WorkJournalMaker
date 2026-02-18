# Cluster C: LLM Client Consolidation — Implementation Tracker

**Plan:** `plan.md`
**Source:** `improvements.md` items #2, #6, #8, #9
**Branch:** `improvements/cluster-c-llm-consolidation`

## Steps

- [x] **Step 1:** Extract `BaseLLMClient` with shared logic ([#56](https://github.com/lbnl-science-it/WorkJournalMaker/issues/56))
- [ ] **Step 2:** Add `CBORGConfig` and CBORG client ([#57](https://github.com/lbnl-science-it/WorkJournalMaker/issues/57))
- [ ] **Step 3:** Add provider fallback to `UnifiedLLMClient` ([#58](https://github.com/lbnl-science-it/WorkJournalMaker/issues/58))
- [ ] **Step 4:** Wire fallback into CLI and verify end-to-end ([#59](https://github.com/lbnl-science-it/WorkJournalMaker/issues/59))
