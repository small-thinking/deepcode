# DeepCode repository instructions

These rules supplement the global Codex instructions.

## Start from current code

Before editing code or problem definitions, assume the local checkout may be stale. At the start of each coding task, and when resuming edits after other work may have advanced the repository:

1. Inspect `git status --short --branch` and identify the task's branch/worktree. Preserve all existing changes.
2. Run `git fetch origin` and compare the task branch with the current `origin/main`.
3. For a new task, create its feature branch from the freshly fetched `origin/main`. If updating a clean local `main` checkout, use `git pull --ff-only origin main`.
4. For an existing task branch, integrate newer `origin/main` changes with an appropriate merge or rebase before continuing edits. Preserve task-owned uncommitted changes with a recoverable method when needed, and resolve conflicts without discarding either side. Do not blindly pull into a dirty or unrelated checkout.

Fetch again before publishing a PR or merging, check for newly landed changes, and rerun affected validation if integration changes the code. If the remote cannot be reached, state the freshness limitation; do not describe the checkout as up to date.

Keep implementation on a feature branch or isolated worktree. Never reset, overwrite, or automatically stash unrelated work merely to refresh the repository.

## Keep problem descriptions concise

Prioritize the task, required input/API contract, a compact example or comparison table, and a few focused follow-up questions. Put extended explanations and derivations in linked references or existing demos instead of repeating them in descriptions. Keep every behavior required by the tests specified, even when shortening the prose.
