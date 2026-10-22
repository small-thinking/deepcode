# GRPO family coding progression — 2026-10-19

Keep the two existing exercises and one staged exercise, rather than duplicating four training loops.

| Exercise | Responsibility | What it does not assess |
| --- | --- | --- |
| 247: Group-Relative Policy Gradient and KL | Causal token scoring, masks, advantage grouping, exact reverse KL | Old-policy ratios, clipping, generation, optimizer lifecycle |
| 489: Debug a GRPO Training Loop | Categorical rollout, frozen old scores, sign-sensitive clipping, SGD, fixed reference | Multi-token causal generation, response lengths, sequence aggregation |
| 522: GRPO Family: Shared Loss, Dr. GRPO, DAPO, and GSPO | Shared multi-token loss, changed advantages/denominators, sequence ratios, soft length penalties | Production generation engines, distributed normalization, model-scale training results |

The family exercise is General practice derived from papers, without company occurrence or frequency attribution. Follow-ups are authored rehearsal prompts. Extended derivations remain in linked references.

The common interface uses current/old log-probabilities `[B,G,T]`, one reward per response, and a boolean response mask. Five stages reuse those tensors and the supplied clipping helper:

1. GRPO: population-standardized advantages, token ratios/clipping, then mean within each response and across responses.
2. Dr. GRPO: remove std scaling and use a supplied global length constant.
3. DAPO loss: asymmetric clipping and the official verl recipe's mini-batch token mean.
4. GSPO: exponentiate mean token log-ratios, clip whole responses, and average response surrogates.
5. DAPO soft-overlong rewards: shape rewards before advantage computation.

All objective kernels use beta=0 to isolate the changed mechanisms. This does not redefine the earlier exercises' exact KL directions. The prompt distinguishes rollout/old policy from reference policy, and the mini-batch token mean from the DAPO paper's group-local denominator.

Technical sources: [DeepSeekMath §4.1](https://arxiv.org/html/2402.03300v3), [Dr. GRPO §3.2](https://arxiv.org/html/2503.20783v2), [DAPO §§3.1–3.4](https://arxiv.org/html/2503.14476v2), [GSPO §4.1](https://arxiv.org/html/2507.18071v2), and the [official verl DAPO recipe](https://github.com/verl-project/verl-recipe/blob/main/dapo/README.md).

## Scope clarification — 2026-10-21

Stage 5 now contains only `soft_overlong_rewards`. Its `buffer_length` parameter
is the width of the linear penalty ramp below `max_length`, unrelated to KV cache.
The penalty is zero through `max_length-buffer_length`, linear to -1 at
`max_length`, and saturated thereafter. The four loss variants are unchanged.

Visible penalty checks keep positional calls compatible with existing saved
solutions using the former parameter name; contract coverage also exercises the
new `buffer_length` keyword. No editor migration or practice-data rewrite is
needed. Modified drafts remain under existing starter-refresh and History
preservation behavior.

## Validation

The reference solution is checked through DeepCode's actual `ml_torch_modeling`
evaluator. Twelve visible checks cover the four reductions, sign-sensitive
clipping, geometric sequence ratios, extreme masked padding, detached old
scores/rewards, constant/singleton groups, and penalty boundaries. The integration
check scores causal tokens and performs two updates on frozen old scores for
each variant. Eleven deliberately wrong algorithms are rejected by arithmetic
and gradient checks. Local deployment must use the merged revision and preserve
existing user-state, custom-test, and activity-log paths.
