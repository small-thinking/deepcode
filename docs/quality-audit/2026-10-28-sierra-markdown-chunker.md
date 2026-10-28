# Sierra Markdown chunking contract review

Scope: `markdown-header-chunker` only, adapted from the supplied `Sierra.md` section titled “Markdown Chunking.” The document is source material; its solution notes do not authorize unrelated changes. Existing interview links and frequency metadata are unchanged. This revision does not establish another interview occurrence.

## Contract

The prompt now reads as a compact interview exercise with a concrete API and the document's four-chunk example. `max_size` measures UTF-8 bytes, including headings and separators. Each stripped nonempty body line is an indivisible paragraph. Greedy packing shares common headings inside a chunk and restores the complete active breadcrumb at every new chunk. Heading levels replace siblings and descendants rather than using stack positions as levels.

The document flags limitations in its own implementation. This exercise explicitly assumes each paragraph plus its full breadcrumb fits. Oversized-paragraph splitting, multiline paragraph recognition, and breadcrumb trimming remain discussion follow-ups. The old fenced-code, character-slicing, and invalid-budget requirements were removed from both the prompt and tests. This is a bounded interview exercise, not a full Markdown parser.

## Coverage

Nine executable cases cover the supplied example, exact-fit greedy packing, parent/child/sibling packing, stale-heading removal after sibling and root changes, skipped heading levels, multibyte Chinese and emoji, whitespace normalization, text before a heading, and no body text. Expected chunk lists are explicit; byte-limit assertions include all emitted context and newlines. There are no stress cases or invalid-input puzzles.

The reference fixture loads the adjacent `solution.py` and runs through the real evaluator. A separate mutation check confirmed that these cases reject character counting, unnecessary repeated context, missing context after a split, stale descendant headings, and strict-less-than budget comparisons.

## Validation

- Focused evaluator and problem-store checks: 28 passed, including all nine challenge cases.
- Browser preview: checked the interview wording, readable multiline input/output, and matching starter signature on an isolated port with temporary practice-state paths.
- Full regression and CI results are recorded on the PR. The merged revision and local service must be verified separately before reporting deployment complete.

## Isolation

Changes were made in a separate worktree based on freshly fetched `origin/main`. The original checkout's GRPO changes were not moved, stashed, or committed. Deployment retains the canonical user-state, custom-test, and activity-log paths and uses a clean checkout of merged main.
