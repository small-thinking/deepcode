# GRPO family coding progression — 2026-10-19

Keep the two existing exercises and add one staged exercise, rather than duplicating four training loops.

| Exercise | Responsibility | What it does not assess |
| --- | --- | --- |
| 247: Group-Relative Policy Gradient and KL | Causal token scoring, masks, advantage grouping, exact reverse KL | Old-policy ratios, clipping, generation, optimizer lifecycle |
| 489: Debug a GRPO Training Loop | Categorical rollout, frozen old scores, sign-sensitive clipping, SGD, fixed reference | Multi-token causal generation, response lengths, sequence aggregation |
| 522: GRPO Family: Shared Loss, Dr. GRPO, DAPO, and GSPO | Shared multi-token loss, changed advantages/denominators, sequence ratios, bounded DAPO group collection and soft length penalties | Production generation engines, distributed normalization, model-scale training results |

The new exercise is General practice derived from papers. It has no company occurrence or frequency attribution. Follow-ups on all three problem pages are explicitly authored rehearsal prompts. Existing evaluator signatures, tests, starter code, demos, and saved drafts are unchanged.

The common interface uses already gathered current/old log-probabilities `[B,G,T]`, one reward per response, and a boolean response mask. The five stages use the same tensors and supplied clipping helper:

1. GRPO: population-standardized advantages, token ratios/clipping, then mean within each response and across responses.
2. Dr. GRPO: remove std scaling and use a supplied global length constant.
3. DAPO loss: asymmetric clipping and the official verl recipe's mini-batch token mean.
4. GSPO: exponentiate mean token log-ratios, clip whole responses, and average response surrogates.
5. DAPO recipe helpers: add soft length penalties; retain complete mixed-correctness groups and refill with a bounded callback budget.

All objective kernels use beta=0 to isolate the changed mechanisms. This does not redefine the earlier exercises' exact KL directions. The prompt distinguishes rollout/old policy from reference policy, and the mini-batch token mean from the DAPO paper's group-local denominator.

Technical sources: [DeepSeekMath §4.1](https://arxiv.org/html/2402.03300v3), [Dr. GRPO §3.2](https://arxiv.org/html/2503.20783v2), [DAPO §§3.1–3.4](https://arxiv.org/html/2503.14476v2), [GSPO §4.1](https://arxiv.org/html/2507.18071v2), and the [official verl DAPO recipe](https://github.com/verl-project/verl-recipe/blob/main/dapo/README.md).

## Validation

- The reference solution passes all 15 new visible checks through DeepCode's actual `ml_torch_modeling` evaluator.
- Hand-computed values and gradients distinguish the four reductions, positive/negative clipping, geometric/arithmetic sequence ratios, and per-prompt/mini-batch token means.
- Checks also cover extreme masked padding, detached old scores/rewards, immutable snapshots, constant/singleton groups, penalty boundaries, whole-group refill, repeated prompt IDs, and retry exhaustion.
- An integration check gathers causal selected-token scores from vocabulary logits and performs two optimizer updates on frozen old scores for each variant.
- Thirteen deliberately wrong algorithms are rejected by the corresponding arithmetic/gradient checks.
- GRPO contract regression tests: 9 unittest methods passed. Problem-store tests: 27 methods passed.
- Browser inspection confirmed the prompt, cross-links, comparison table, starter, follow-ups, and 15 individually runnable checks load in the isolated preview on port 8852.

Before publication, browser validation used an isolated preview on port 8852. The primary checkout's pre-existing uncommitted work was preserved. Local deployment after merge must use the verified merged revision and retain the existing user-state, custom-test, and activity-log paths.

The repository-level `AGENTS.md` now requires fetching current upstream code before editing, updating a clean main checkout with `pull --ff-only`, and integrating current main into an existing task branch without overwriting unrelated work.
