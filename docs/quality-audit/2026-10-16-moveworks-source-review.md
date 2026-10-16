# Moveworks MLE source reconciliation — 2026-10-16

Scope: confirmed MLE / ML infrastructure reports and a separately labeled SWE scoring supplement. The Notion source review records access, event lineage, exact URLs, and unread continuation: https://app.notion.com/p/3fb6ce51456d81de9704cd26fbf8c15f

| Exercise | Evidence and reconstruction boundary |
| --- | --- |
| hangman-next-letter | MLE report supplies word-presence, total-occurrence, alphabetical ordering; standard all-occurrences-revealed behavior and empty return are explicit practice conventions. |
| shortest-unique-substring-highlighting | The 2022 report links a public shortest, case-insensitive substring problem; the 2025 report adds bracket output but does not say shortest. Earliest-start tie-breaking is local. |
| iphone-app-recommendation | Original gives only the recommendation scenario; data, model, deployment and evaluation in the reference are preparation guidance. |
| llm-provider-routing-layer | Original gives internal services, a shared routing layer and providers; reference policies and failure semantics are design choices. |
| failed-project-expectations | Two related questions in the same interview are consolidated. The answer is a framework, not an invented personal story. |
| string-distinctiveness-scoring | Complete concentration/Jaccard formula comes from SWE sources. It does not resolve the incomplete MLE scoring prompt. Output order and group-wise exclusion for tied winners are local conventions. |

The incomplete MLE common-letter scoring prompt remains Notion-only. A text-justification report has an MLE title but SWE role metadata; it is retained as an unresolved lead. Vague calculator and recommender mentions are insufficient for additional exercises. Generic prep pages are not candidate evidence.

Validation: all three executable exercises pass their visible cases through the evaluator and browser; written prompts, reference-answer tabs, source links, frequency tiers and the company hub were checked. The full suite passed except for one sandbox-denied local socket test, which passed on its targeted rerun with socket access. No application code or dependencies changed.

Delivery: isolated local worktree and preview on port 8851. No commit, push, PR, merge, or publication performed by this run.

## Second-pass expansion and correction

The user-facing preview inherited the first pass's three completed coding-validation statuses and four activity events. Those exact test records were backed up and removed, and the three editors reset to starters. The primary checkout had no corresponding Moveworks progress. New browser checks use port 8852 with separate state files; port 8851 is left unstarted for the user.

Added source-backed supplements: citation-range-merging, synonym-query-rewrites, text-justification, restaurant-review-keyword-search, document-scoped-assistant-product, and word-break-sentences. Role differences remain visible. Existing generic RAG/component exercises were compared; the new document-assistant question focuses on user configuration and product lifecycle rather than only retrieval internals. Word Break sentence enumeration is distinct from the existing word ladder and grid word-search tasks.

All finite-index reports were body-attempted, with a deleted-body limitation. Two bounded forum searches and public candidate reports supplied further corroboration, including visually checked public images for sentence segmentation and a generic billing design lead. Unrelated frontend, billing, car-rental and role-uncertain campus leads remain in the research record rather than being labeled MLE exercises.

The 2026 SWE three-stage scoring report does not define its callback formula or exclusion/aggregation rules. Its structure helps preparation but does not prove the 2025 MLE prompt is the same as the complete two-part SWE multiset Jaccard version. No fixed tests were fabricated for the incomplete MLE task.

Validation after expansion: all 471 tests passed. Seven executable exercises have 44 visible cases; the four added coding exercises passed browser checks in the separate QA environment, and both new written reference-answer tabs rendered. Text-justification snippets assert exact spacing because the generic stdout comparator normalizes whitespace; a wrong-padding submission is rejected. No application code or dependencies changed.
