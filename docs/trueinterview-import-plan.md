# TrueInterview Import Plan

This document is the shared, durable plan and progress ledger for importing
TrueInterview interview intelligence into DeepCode. Update it as each batch is
audited, implemented, verified, and merged.

Last scope verification: 2026-08-16

## Goal

Import every accessible, sufficiently specified, DeepCode-compatible question
from the in-scope TrueInterview companies without duplicating existing problem
contracts. Preserve interview-process evidence separately from executable
problems, and quantify the value of paid TrueInterview access before purchasing
it.

## Source and Scope

The company scope comes from the Opportunity 2026 `Companies` database. Rows
with `Interview Priority` 1-3 are in scope; `4 - Skip / No Interview Value` is
out of scope.

Opportunity 2026 currently contains 18 in-scope companies:

- Serious Prep: Anthropic, Google DeepMind, Luma AI, OpenAI, Runway, Thinking
  Machines Lab.
- Targeted Prep: Airbnb, Faire, Harvey, Mistral AI, Reflection AI, Sierra.
- Practice / Calibration: Abridge, OpenEvidence, Plaud, Reducto,
  SpaceXAI / xAI-related roles, XDOF.

TrueInterview's 48-company directory covers only five of those companies:

| Execution order | Opportunity company | TrueInterview company | Public problems | Earlier directory modules | Current DeepCode problems |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | SpaceXAI / xAI-related roles | xAI | 35 | 4 | 0 |
| 2 | Harvey | Harvey | 9 | 3 | 2 |
| 3 | Airbnb | Airbnb | 34 | 3 | 0 |
| 4 | Anthropic | Anthropic | 67 | 5 | 5 |
| 5 | OpenAI | OpenAI | 80 | 5 | 23 |

Problem counts above are the public-homepage figures verified on 2026-08-16.
They already differ from the earlier authenticated company-directory snapshot,
so every future authorized audit must save its date, page, and counting method
instead of treating these numbers as stable inventory totals.

The other 13 in-scope companies are absent from the TrueInterview directory:
Abridge, Faire, Google DeepMind, Luma AI, Mistral AI, OpenEvidence, Plaud,
Reducto, Reflection AI, Runway, Sierra, Thinking Machines Lab, and XDOF.
TrueInterview has a separate Google entry, but it must not be treated as Google
DeepMind without company-level evidence.

## Access Boundary

The currently connected TrueInterview account is on the Free plan.

- Accessible free coding questions may expose the prompt, contract, starter
  code, provided runner, visible input/expected-output cases, solution, and
  linked interview experiences.
- Member questions expose only limited metadata behind the current account's
  upgrade gate. Do not infer hidden prompts, tests, or solutions.
- Visible TrueInterview cases are source examples, not evidence that hidden
  submission tests are available or that the contract is complete.
- Do not bypass membership gates, login barriers, CAPTCHA, or safety
  interstitials.

Record every question as `free`, `member-gated`, or `unknown`. A paid-access
recommendation must be based on reconciled counts for the five covered
companies, the proportion of gated questions that are likely runnable in
DeepCode, the official price and renewal terms, and the amount of genuinely new
content after semantic deduplication.

### Official plan comparison

Verified from the official [Plans & Pricing](https://trueinterview.io/premium)
page on 2026-08-16:

| Plan | Monthly | Three months | Annual | Full company question banks |
| --- | ---: | ---: | ---: | --- |
| Free | $0 | n/a | n/a | No; only the first questions for a company/round |
| Pro | $39 | $89 | $149 | No |
| Insider | $69 | $159 | $299 | Yes |

Both paid tiers advertise a seven-day trial. Checkout requires a card, the
first charge is described as occurring after the trial, cancellation during the
trial is described as free, and cancellation after payment retains access
through the paid period. The public pages do not clearly guarantee that every
company question has a visible raw test suite, document taxes/refunds in
detail, or provide an export/download feature. `Real tests` means server-side
judging and must not be interpreted as downloadable hidden tests.

For this project, Pro is not the relevant upgrade because it does not unlock
the complete company banks. The only potentially relevant temporary upgrade is
Insider Monthly, currently advertised at $69, and it should not be purchased
until the authorization gate below is cleared.

## Authorization Gate

The official [Terms of Service](https://trueinterview.io/terms), updated
2026-07-15, prohibit scraping, data mining, automated access, extracting the
site's structure/taxonomy/arrangement, and extracting a substantial portion of
the service. A subscription grants access; it does not grant permission to
republish problem statements, tests, or solutions in a GitHub repository.

Accordingly, the planned automated five-company inventory and corpus import are
paused. Do not resume browser enumeration, purchase a subscription for this
purpose, or add TrueInterview-derived repository content until TrueInterview
provides written permission covering the intended use.

The permission request should ask whether the user may:

1. use an automated browser to inventory the five named company banks;
2. store source metadata and access status in a private local repository;
3. create independently worded, runnable derivative exercises and tests;
4. publish those derivative exercises in the public DeepCode GitHub repository;
5. cite canonical TrueInterview URLs and company associations;
6. use an official export/API instead of browser automation; and
7. receive the full Insider feature set during the advertised trial.

Recommended contact: `kevin@trueinterview.io`. Keep private/internal permission
and public-republication permission as separate questions; approval for one
does not imply the other.

Suggested permission email:

```text
Subject: Permission request for a personal TrueInterview-to-DeepCode study project

Hi Kevin,

I use TrueInterview for personal interview preparation and maintain an
open-source local coding-practice project called DeepCode. I would like to
audit the xAI, Harvey, Airbnb, Anthropic, and OpenAI question banks, identify
questions not already represented in DeepCode, and create independently
worded, runnable practice exercises with my own reference implementations and
tests.

Could you clarify whether I have permission to:

1. use an automated browser to inventory those five company banks;
2. store question metadata and canonical TrueInterview URLs in a private local
   repository;
3. create derivative exercises for private personal use; and
4. publish independently worded derivative exercises and tests in DeepCode's
   public GitHub repository?

If browser automation is not permitted, is there an official export or API I
may use? Also, does the seven-day Insider trial immediately include the full
company question banks?

I will not reproduce TrueInterview editorial solutions verbatim or attempt to
access hidden server-side tests. I am happy to follow attribution, rate-limit,
or non-public-use conditions you specify.

Thank you.
```

## Source Identity and Deduplication

TrueInterview reports more company-question associations than unique
questions. Use the canonical `/questions/<slug>` slug as the source identity and
store companies as a multi-value association. Never create one DeepCode problem
per company when the source slug and contract are shared.

For every source question, compare in this order:

1. Exact source identity: canonical TrueInterview slug and normalized source
   URL.
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
| Exact duplicate | Keep the existing slug; add missing company/source metadata or tests only. |
| Same contract with missing behavior | Strengthen the existing prompt/tests/reference solution. |
| Small follow-up on the same API | Keep one multipart problem when it remains a 45-60 minute exercise. |
| New API, state model, or substantial follow-up | Create a separate series problem and stable slug. |
| Related algorithm but different contract | Preserve separate problems and connect them with tags/series. |
| Gated, ambiguous, or unsupported | Record it in the manifest; do not fabricate a runnable problem. |

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

Interview processes, candidate-report synthesis, access state, and import
decisions belong under:

```text
docs/interview-intelligence/trueinterview/
  README.md
  question-manifest.jsonl
  companies/
    xai.md
    harvey.md
    airbnb.md
    anthropic.md
    openai.md
```

Company documents should preserve role, seniority, round sequence, format,
duration, reported date, source URL, and contradictions between reports. Do not
combine different candidate reports into a fictional standard interview loop.
Do not mirror paid editorial prose or solutions verbatim; author an independent
DeepCode contract and implementation from the accessible evidence.

## Per-Company Workflow

This workflow is contingent on written authorization for the relevant access,
storage, derivative-work, and publication scope.

1. Reconcile company-page problem/module counts and enumerate all question
   associations.
2. Deduplicate the association list by canonical question slug.
3. Record title, companies, category, difficulty, role/round metadata, access
   state, visible artifact fields, and source URLs in the manifest.
4. Classify each question as runnable, documentation-only, duplicate,
   member-gated, ambiguous, or unsupported.
5. Cross-check runnable candidates against DeepCode and `All Interview
   Questions`.
6. Normalize the prompt and starter code without adding unstated behavior.
7. Recreate every visible source case semantically, then add deterministic
   contract and edge-case coverage.
8. Write an independent reference solution and run all tests.
9. Run focused and full repository checks, then verify the live API and browser
   rendering with temporary user state.
10. Merge the focused PR before advancing that batch's checkpoint.

## Test-Case Acceptance

Each imported runnable question should cover:

- all accessible TrueInterview visible cases;
- at least one normal contract path;
- contract-defined boundaries and tie-breaking;
- state isolation, ordering, expiry, replay, or atomicity when applicable;
- deterministic seeds, shapes, and dtypes for NumPy/PyTorch problems;
- only the invalid-input behavior explicitly supported by the source contract.

Use `ml_coding` for deterministic stdout comparisons, `ml_modeling` for
assertion-based behavioral/stateful checks, `ml_torch_modeling` for small
CPU-friendly Torch checks, and `ml_torch_lab` only when a committed hidden
harness and local data flow are justified. Ordinary committed `tests.json`
cases are visible in the DeepCode UI.

## Batches and Pull Requests

Keep browser inventory read-only and serialize repository integration so IDs,
slugs, fixtures, and checkpoints cannot race.

1. Obtain written authorization and record its exact scope.
2. Plan and import infrastructure.
3. xAI pilot: inventory all current associations, then complete at most two free
   questions end to end, including one negative duplicate/gated/unsupported
   decision.
4. Remaining accessible xAI deltas.
5. Harvey inventory.
6. Airbnb inventory.
7. Anthropic inventory.
8. OpenAI inventory.
9. Re-evaluate gated, runnable, non-duplicate counts and make the paid-access
   recommendation.
10. If paid access is explicitly approved and activated by the user, resume only
   the gated manifest rows in the same company order.

Use one focused PR for a small company batch. Split dense Anthropic/OpenAI work
into related groups of roughly three to five problem families. Do not create a
single corpus-sized PR.

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
rendered prompt/starter/tests/source links, run the reference solution, check the
browser console, and stop the service before finishing.

## Stop Conditions

Stop the affected item and record the blocker when encountering login loss,
CAPTCHA, a membership gate, hidden tests, a prompt/test contradiction,
insufficient contract evidence, a semantic dedupe ambiguity, a required new
evaluator or undeclared dependency, an unsupported runtime, or a non-whitelisted
page/trap link.

## Progress Ledger

| Batch | Inventory | Dedupe | Implementation | Verification | PR / status |
| --- | --- | --- | --- | --- | --- |
| Shared plan | complete | n/a | complete | complete | PR #53 merged |
| Official Free/paid audit | complete | n/a | n/a | complete | Insider required for full banks |
| Authorization request | blocked on external permission | n/a | n/a | pending | required before automated access/import |
| Five-company inventory | paused | pending | n/a | pending | Terms authorization gate |
| xAI pilot | paused | pending | pending | pending | Terms authorization gate |
| xAI remaining | pending | pending | pending | pending | not started |
| Harvey | pending | pending | pending | pending | not started |
| Airbnb | pending | pending | pending | pending | not started |
| Anthropic | pending | pending | pending | pending | not started |
| OpenAI | pending | pending | pending | pending | not started |
| Paid-access decision | pending | pending | n/a | pending | not started |
