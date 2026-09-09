# Question quality audit

Snapshot: 2026-09-08 UTC / 2026-09-07 America/Los_Angeles, starting from fetched `origin/main` commit `4ffda48`.

This is the first completed batch, not a claim that the full question bank has been audited. [inventory.jsonl](inventory.jsonl) lists all **297 committed questions** with category, audit group, evaluator, test applicability, base and reviewed visible case counts, source links, latest definition-file commit and per-question progress. Counts of cases are triage hints only, not evidence that a suite is weak or strong.

| Audit group | Questions |
| --- | ---: |
| Coding | 167 |
| ML Coding | 55 |
| Modeling / lab | 2 |
| System Design | 39 |
| ML System Design | 28 |
| Other discussion (behavioral / explanatory) | 6 |

The evaluator name `ml_modeling` is used by many ordinary Coding questions; it is not a content classification. All 73 `system_design` evaluator questions are writing exercises without executable cases. The remaining 224 have a code evaluation mechanism; private/local-data labs need separate fixture and harness verification without inspecting private contents.

## Batch progress

**21 reviewed: 15 repaired, 6 reviewed unchanged; 276 not yet reviewed.** Source-chain gaps remain for some reviewed entries and are recorded separately from repair status.

- [Coding evidence and tests](2026-09-08-coding.md): 383, 385, 386, 387. Separate branch `codex/quality-coding-contracts-20260908`.
- [ML Coding evidence and tests](2026-09-08-ml.md): 366, 367, 371, 372. Separate branch `codex/quality-ml-contracts-20260908`.
- [Design/source evidence, including unchanged experiment review](2026-09-08-design.md): 373–382, 384, 393, 394. Branch `codex/question-quality-audit-20260908`.

The documents for independent batches arrive through their separate PRs; the ledger describes completed local reviews, not proof that every PR has merged. Verify PR/commit state before continuing.

## Scope preserved outside the snapshot

The primary checkout `/Users/Yexi/source/deepcode` was on `codex/anthropic-interview-sync` at `54fc137` with user changes. Those changes were left in place. Its untracked **392 GRPO Training Loop Debugging** is an additional local question, not part of this committed-main inventory and **not reviewed** in this audit. Primary-worktree variants of 106, 109, 247, 320 and 389 likewise were not overwritten or treated as audited by testing the clean main-based copy. The Anthropic company edit, 109 assets and untracked reference/test files were preserved.

## Next batches

1. Recent remaining executable questions: 354–365 and 368–370, focusing on source fidelity and whether tests distinguish behavior rather than merely checking shape.
2. Current-main 388–391 attention/network family, then older long-form ML descriptions. Preserve the user's separate 389 test changes while reviewing the main version.
3. Expand across older Coding, ML and design categories using `last_definition_commit` and `triage_flags`, rather than assuming numeric IDs are chronological.

Whole-catalog structural triage found no prompt containing the scanned unsupported LaTeX commands/display delimiters or an odd number of triple-backtick fences. ID 313 contains a literal `\n` and is flagged for contextual inspection, not automatically declared broken. These checks do not prove that all formulas or Markdown render correctly; that requires per-question review and actual UI inspection.

To resume, filter rows whose `status` is `not_reviewed`; separately revisit source statuses containing `blank`, `unverified` or `unavailable`. A newly accessible original should update evidence before changing contracts. Preserve explicit, reasonable practice choices where the source is abbreviated. Every additional test needs an independent expected-result argument and a specific plausible mistake it detects.

Structural identity check also found metadata ID `141` reused by `batched-llm-inference-service` and `moderator-list-hierarchy`. Their slugs and UI-generated display IDs are separate. Both remain pending content review; the ledger uses the unique slug/path for identity and flags the duplicate rather than renumbering stable metadata without tracing its consumers.

## Combined verification

A temporary detached checkout combined Coding merge `8a8de36`, ML commit `989352e`, and design commit `65afbf2` without changing shared `main`. `UV_CACHE_DIR=/private/tmp/deepcode-quality-uv-cache UV_PROJECT_ENVIRONMENT=/Users/Yexi/source/deepcode/.venv uv run --no-sync python -m unittest discover -s tests` passed **all 362 tests** in 84.860 seconds with localhost permission. Log: `/private/tmp/deepcode-quality-integrated-tests.log`. Later ledger wording/count-field edits do not change the tested problem or test files. All temporary preview services were stopped.
