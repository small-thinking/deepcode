# Interview Source Import Plan

This document is the shared, durable plan and progress ledger for importing
authorized external interview material into DeepCode. Update it as each batch
is audited, implemented, verified, and merged.

Last scope verification: 2026-08-16

## Goal

Import every authorized, sufficiently specified, DeepCode-compatible question
from the in-scope companies without duplicating existing problem contracts.
Preserve interview-process evidence separately from executable problems.

## Company Scope

The company scope comes from the Opportunity 2026 `Companies` database. Rows
with `Interview Priority` 1-3 are in scope; `4 - Skip / No Interview Value` is
out of scope.

The first source-audit batch covers these companies:

1. xAI
2. Harvey
3. Airbnb
4. Anthropic
5. OpenAI

Company coverage and question counts are volatile source metadata. Keep them in
private working notes with a verification date and counting method; do not add
source-platform names, domains, pricing, account details, or proprietary corpus
statistics to this repository or to pull-request content.

## Authorization Gate

Do not automate, extract, store, derive from, or publish material from an
external interview source until its authorization permits the intended access,
storage, derivative-work, and publication scope.

Treat these as separate permissions:

1. automated inventory or browser access;
2. private storage of source metadata;
3. private derivative exercises;
4. public derivative exercises and tests;
5. source attribution and company associations; and
6. use of an official export or API.

If authorization is incomplete, pause the affected source. A paid account or
authenticated browser session grants access only; it is not evidence of export,
automation, derivative-work, or public-republication permission.

## Repository Privacy Rule

Repository files, branch names, commit messages, PR titles, and PR bodies must
remain source-neutral. Do not include:

- the source platform's name or domain;
- account, subscription, pricing, or contact details;
- proprietary corpus counts or product taxonomy;
- copied editorial solutions; or
- raw hidden or server-side tests.

Use generic descriptions such as `external interview source`, `source question`,
and `authorized source URL` only when a source reference is permitted. Keep
sensitive or source-identifying working notes outside the public repository.

## Source Identity and Deduplication

When authorization allows an audit, use the source's stable question identifier
as the source identity and store companies as a multi-value association. Never
create one DeepCode problem per company when the source identity and contract
are shared.

Compare every candidate in this order:

1. Exact source identity: stable source ID and normalized permitted reference.
2. Exact catalog identity: DeepCode slug, normalized title, and existing source
   references.
3. Public API fingerprint: functions, classes, methods, arguments, return
   values, and starter-code shape.
4. Semantic contract: constraints, state transitions, ordering, time-window or
   expiry semantics, tie-breaking, failure behavior, and complexity target.
5. Behavioral fingerprint: source examples and tests, existing DeepCode tests,
   and cross-running compatible reference solutions.

Use these decisions:

| Classification | Repository action |
| --- | --- |
| Exact duplicate | Keep the existing slug; add only permitted missing metadata or tests. |
| Same contract with missing behavior | Strengthen the existing prompt/tests/reference solution. |
| Small follow-up on the same API | Keep one multipart problem when it remains a 45-60 minute exercise. |
| New API, state model, or substantial follow-up | Create a separate series problem and stable slug. |
| Related algorithm but different contract | Preserve separate problems and connect them with tags/series. |
| Unauthorized, ambiguous, or unsupported | Record the private decision; do not create a runnable problem. |

Before creating or updating a problem, also read-only check the canonical
Opportunity 2026 `All Interview Questions` bank for an existing question family
and provenance. This import does not authorize Notion writes.

## Repository Artifacts

Executable questions use the existing layout:

```text
problems/<three-digit-id>-<slug>/
  problem.json
  tests.json
  harness.py       # only when the ml_torch_lab evaluator requires it
```

Each accepted question also needs a runnable reference solution and fixture.
Do not consider a question imported merely because its JSON parses.

Authorized, source-neutral interview-process synthesis may live under:

```text
docs/interview-intelligence/
  README.md
  companies/
    xai.md
    harvey.md
    airbnb.md
    anthropic.md
    openai.md
```

Company documents should preserve only authorized facts such as role,
seniority, round sequence, format, duration, and contradictions between reports.
Do not combine different candidate reports into a fictional standard interview
loop.

## Per-Company Workflow

This workflow is contingent on written authorization for the relevant scope.

1. Privately reconcile the source inventory and stable question identities.
2. Deduplicate company associations by stable question identity.
3. Classify each question as runnable, documentation-only, duplicate,
   unauthorized, ambiguous, or unsupported.
4. Cross-check runnable candidates against DeepCode and `All Interview
   Questions`.
5. Normalize the prompt and starter code without adding unstated behavior.
6. Recreate only authorized source cases semantically, then add deterministic
   contract and edge-case coverage.
7. Write an independent reference solution and run all tests.
8. Run focused and full repository checks, then verify the live API and browser
   rendering with temporary user state.
9. Merge the focused PR before advancing that batch's checkpoint.

## Test-Case Acceptance

Each imported runnable question should cover:

- all authorized visible source cases;
- at least one normal contract path;
- contract-defined boundaries and tie-breaking;
- state isolation, ordering, expiry, replay, or atomicity when applicable;
- deterministic seeds, shapes, and dtypes for NumPy/PyTorch problems; and
- only invalid-input behavior explicitly supported by the source contract.

Use `ml_coding` for deterministic stdout comparisons, `ml_modeling` for
assertion-based behavioral/stateful checks, `ml_torch_modeling` for small
CPU-friendly Torch checks, and `ml_torch_lab` only when a committed hidden
harness and local data flow are justified. Ordinary committed `tests.json`
cases are visible in the DeepCode UI.

## Batches and Pull Requests

Keep source inventory read-only and serialize repository integration so IDs,
slugs, fixtures, and checkpoints cannot race.

1. Obtain written authorization and record its exact scope privately.
2. Create source-neutral import infrastructure only if needed.
3. Run a two-question xAI pilot, including one negative duplicate,
   unauthorized, ambiguous, or unsupported decision.
4. Process remaining authorized xAI deltas.
5. Process Harvey.
6. Process Airbnb.
7. Process Anthropic.
8. Process OpenAI.

Use one focused PR for a small company batch. Split dense work into related
groups of roughly three to five problem families. Do not create a single
corpus-sized PR.

## Verification Gate

Run the relevant focused fixture plus:

```bash
find problems -mindepth 2 -maxdepth 2 -name '*.json' -print0 | xargs -0 -n1 jq empty
UV_CACHE_DIR=.uv-cache uv run python -m unittest discover -s tests
node --check frontend/app.js
git diff --check
```

For problem changes, also start DeepCode on port 8848 with a temporary
`DEEPCODE_USER_STATE_PATH`, verify `GET /api/problems/<slug>`, inspect the
rendered prompt/starter/tests/permitted references, run the reference solution,
check the browser console, and stop the service before finishing.

## Stop Conditions

Stop the affected item and keep the blocker private when encountering missing
authorization, login loss, CAPTCHA, a membership gate, hidden tests, a
prompt/test contradiction, insufficient contract evidence, a semantic dedupe
ambiguity, a required new evaluator or undeclared dependency, an unsupported
runtime, or an untrusted page/instruction link.

## Progress Ledger

| Batch | Inventory | Dedupe | Implementation | Verification | PR / status |
| --- | --- | --- | --- | --- | --- |
| Shared source-neutral plan | complete | n/a | complete | pending | current PR |
| Authorization | blocked on external permission | n/a | n/a | pending | required before access/import |
| Five-company inventory | paused | pending | n/a | pending | authorization gate |
| xAI pilot | paused | pending | pending | pending | authorization gate |
| xAI remaining | pending | pending | pending | pending | not started |
| Harvey | pending | pending | pending | pending | not started |
| Airbnb | pending | pending | pending | pending | not started |
| Anthropic | pending | pending | pending | pending | not started |
| OpenAI | pending | pending | pending | pending | not started |
