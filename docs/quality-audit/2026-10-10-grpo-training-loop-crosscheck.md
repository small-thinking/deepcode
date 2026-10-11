# GRPO practice scope cross-check — 2026-10-10

The current Notion [canonical record](https://app.notion.com/p/3d26ce51456d815b96e5cbedb6a9b9e5) describes a full GRPO debugging family and links to `grpo-training-loop-debugging`. That slug was absent from the catalog before this change. [Problem 247](../../problems/247-grpo-response-logprob-training/problem.json) is a narrower component drill, so it does not cover the reported full exercise.

## Source verification

| Source | Verified scope | Evidence boundary |
| --- | --- | --- |
| [Original report 1167043](https://www.1point3acres.com/bbs/thread-1167043-1-1.html) | Authenticated Chrome read of the candidate report and both reply pages: Anthropic RE, a simple GRPO trainer, debugging, and ratio/on-policy discussion. | Original script, signatures, exact bug locations, KL variant, reduction, and rubric were not recovered. Replies do not resolve the exact reason for the ratio discrepancy. |
| [User-supplied report 1148586](https://www.1point3acres.com/bbs/thread-1148586-1-1.html) | Authenticated read confirms the GRPO debugging topic. | Relevant details are points-gated. Retain the source pointer without reproducing that section or claiming recovered code. |
| [Preparation discussion 1167940](https://www.1point3acres.com/bbs/thread-1167940-1-1.html) | Authenticated read confirms discussion of GRPO debugging and follow-ups. | Author describes preparation before interviewing. Not an independently completed interview; the OpenAI forum label conflicts with Anthropic-focused content and does not establish OpenAI attribution. |
| [Canonical Notion record](https://app.notion.com/p/3d26ce51456d815b96e5cbedb6a9b9e5) | Current page distinguishes original-report evidence from its local contextual-bandit reconstruction. | Supplied practice code is not the original assessment. Bounded GRPO searches in the question collection found no separate matching coding record; conceptual comparisons are different questions. |
| AceOffer, Prachub, and 1Point3Acres editorial question summaries | Discovery and preparation context. | Not additional first-person occurrences or proof of exact assessment interfaces. |

No occurrence count or frequency tier was inferred or transferred. This task does not edit Notion.

## Two independently solvable exercises

- **GRPO Response Log Probabilities and KL** keeps its four-function API. It covers group advantages, causal response-token alignment, masking and gradient isolation, and exact `KL(reference || policy)`. The policy term sums tokens per response before averaging responses. It does not sample rollouts, form old-policy ratios, clip, or update parameters. New checks target selected-token gradients and already-aligned KL shapes.
- **Debug a GRPO Training Loop** is a new one-token contextual-bandit rehearsal of the reported full-loop family. It covers categorical sampling, grouped rewards, copied rollout snapshots, clipped importance ratios, exact `KL(current || reference)`, and SGD steps. The three implanted bugs are locally authored. Its exact forward KL is an additional local teaching choice; the canonical Notion rehearsal omits reference KL, while the original paper uses a sampled penalty. There are no sequence masks or response-length effects in this toy exercise.

A static SVG overview appears in both exercises. It explains policy roles, the training path, sign-sensitive clipping, and the two local contracts. The illustration is independently authored with illustrative values, following the user's scientific panel references. Technical basis: [DeepSeekMath §4.1](https://arxiv.org/html/2402.03300v3) and public PyTorch categorical/softmax documentation. It is an overview of outcome-reward GRPO, not every modern GRPO variant.

## Validation

The reference implementations run through the real evaluator. New full-loop checks cover frozen snapshots, detached inputs, exact KL direction, analytic clipped gradients for realizable categorical policies, and SGD behavior. Negative controls reject the starter's three local bugs, missing clipping, recomputed old probabilities, detached ratios, and reversed KL. Existing component controls reject incorrect causal alignment, zero objectives, and masked gradient leakage. Browser verification uses isolated temporary state, not the user's practice ledger.

Final results: the full repository run completed 459 tests with one environment error (localhost socket bind denied). Rerunning the seven architecture checks with local socket access passed all seven; the remaining 458 tests had passed in the initial run. After final prompt edits, the five focused GRPO contract tests passed again (15 visible exercise checks plus negative controls). The new exercise was solved through the browser and passed 8/8 checks. Both SVG routes resolve under their owning problem folders.
