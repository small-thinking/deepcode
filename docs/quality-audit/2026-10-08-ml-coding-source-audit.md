# ML coding source audit — 2026-10-08

Audited 29 ML Coding exercises whose catalog frequency was absent or unknown. Exact-source evidence, reported families, locally specified extensions, adjacent tasks and general practice were reviewed separately. No independently verified new candidate event was established; missing frequency does not establish exactly one occurrence.

Updated descriptions and background references for all 29 exercises. Fixture slots increased from 98 to 123; existing slots were strengthened where their oracle accepted incorrect gradients. Removed unsupported company tags in 17 exercises. Slugs and callable APIs remain stable. User code, completion state and activity logs are outside this change.

[Private Notion audit](https://app.notion.com/p/3f46ce51456d81c5a531d1a9bd6ed0c1) contains individual source boundaries and background links. Fourteen existing Notion pages received corresponding audit notes; source counts and historical source dates were preserved.

## Per-exercise decisions

| ID | Exercise | Source classification | Notion mapping / related page | Checks |
| --- | --- | --- | --- | --- |
| 1 | [Matrix-Vector Dot Product](http://127.0.0.1:8848/#/problems/matrix-vector-dot-product) | general_math_practice | No exact page recovered | 6 → 6 |
| 16 | [Linear Regression Gradient Step](http://127.0.0.1:8848/#/problems/linear-regression-gradient-step) | general_practice_with_existing_notion_audit | [record](https://app.notion.com/p/3d86ce51456d81f5bf05d3b1f6f65769) | 7 → 7 |
| 108 | [MNIST Torch Classifier](http://127.0.0.1:8848/#/problems/mnist-torch-classifier) | general_training_lab | No exact page recovered | 2 → 2 |
| 242 | [Causal Decoder, Masked Classifier, and Incremental Generation](http://127.0.0.1:8848/#/problems/debug-gpt-classifier-cache) | reported_family_with_local_practice_extensions | [record](https://app.notion.com/p/37a6ce51456d81b8b0c5f9f9f8850820) | 3 → 5 |
| 243 | [Masked Encoder Classifier](http://127.0.0.1:8848/#/problems/masked-transformer-encoder-classifier) | local_practice_exact_origin_unverified | No exact page recovered | 3 → 5 |
| 244 | [Batched Seq2Seq Training and Decoding Utilities](http://127.0.0.1:8848/#/problems/seq2seq-reversal-debug) | local_practice_with_adjacent_curated_background | No exact page recovered | 3 → 5 |
| 245 | [Batched Binary MLP Training Loop](http://127.0.0.1:8848/#/problems/batched-binary-mlp) | local_practice_exact_origin_unverified | No exact page recovered | 3 → 3 |
| 246 | [Noisy Annotator Posterior Inference](http://127.0.0.1:8848/#/problems/noisy-annotator-posterior-refactor) | source_supported_family_local_extension | [record](https://app.notion.com/p/3656ce51456d819da4b7ddd95aa046f1) | 3 → 5 |
| 247 | [Group-Relative Response Log Probabilities](http://127.0.0.1:8848/#/problems/grpo-response-logprob-training) | reconstructed_component_from_secondary_GRPO_family | [record](https://app.notion.com/p/3d26ce51456d815b96e5cbedb6a9b9e5) | 6 → 6 |
| 248 | [Autograd Matrix Products and Chain Gradients](http://127.0.0.1:8848/#/problems/autograd-matmul-chain-scan) | curated_candidate_account_plus_same_lineage_public_reconstruction | [record](https://app.notion.com/p/3ed6ce51456d81a78fd9f41de8dd1d4c); [related](https://app.notion.com/p/3656ce51456d81bca27ce926fa74c9bc) | 3 → 3 |
| 249 | [Noisy Annotator Filtering](http://127.0.0.1:8848/#/problems/noisy-annotator-filtered-training) | source_supported_family_local_preprocessing_variant | [record](https://app.notion.com/p/3656ce51456d819da4b7ddd95aa046f1) | 3 → 5 |
| 250 | [Linear Feature-Dimension Sweep](http://127.0.0.1:8848/#/problems/linear-double-descent-sweep) | general_practice_unverified_company | No exact page recovered | 2 → 3 |
| 251 | [ML Numerics and Loss Curves](http://127.0.0.1:8848/#/problems/ml-numerics-loss-curve-toolkit) | general_practice_unverified_company | No exact page recovered | 3 → 5 |
| 252 | [Robust A/B Experiment Summary](http://127.0.0.1:8848/#/problems/robust-ab-test-analysis) | general_practice_unverified_company | No exact page recovered | 2 → 4 |
| 253 | [Image Data Quality and Finite-Value Repair](http://127.0.0.1:8848/#/problems/image-data-quality-denoising) | general_practice_unverified_company | No exact page recovered | 2 → 3 |
| 262 | [Adversarial Decoding Cutoff Policy](http://127.0.0.1:8848/#/problems/adversarial-decoding-cutoff-policy) | general_practice_unverified_company | No exact page recovered | 5 → 5 |
| 296 | [Deterministic Tool-Calling Agent Session](http://127.0.0.1:8848/#/problems/tool-calling-agent-session) | local_practice_without_exact_interview_provenance | [related](https://app.notion.com/p/36f6ce51456d817786d8cfdbd9f29ff1) | 3 → 5 |
| 298 | [Composable NumPy Image Transformation Pipeline](http://127.0.0.1:8848/#/problems/numpy-image-transformation-pipeline) | related_general_coding_family_local_variant | [record](https://app.notion.com/p/3716ce51456d815c9df1d8c7a560ed3e) | 3 → 3 |
| 299 | [Repair a Masked Batched Gather](http://127.0.0.1:8848/#/problems/masked-batched-gather-repair) | local_practice_without_exact_interview_provenance | No exact page recovered | 3 → 5 |
| 307 | [Deterministic Pair-Merge Tokenizer](http://127.0.0.1:8848/#/problems/deterministic-pair-merge-tokenizer) | local_practice_without_exact_interview_provenance | [related](https://app.notion.com/p/38c6ce51456d81e1a521d314cc94d8cb) | 3 → 4 |
| 308 | [Batched Image Processor](http://127.0.0.1:8848/#/problems/batched-image-processor) | general_numpy_batching_practice | [related](https://app.notion.com/p/3716ce51456d815c9df1d8c7a560ed3e) | 3 → 3 |
| 309 | [Capacity Series Analysis](http://127.0.0.1:8848/#/problems/capacity-series-analysis) | practice_variant_of_non_coding_capacity_analysis | [record](https://app.notion.com/p/3906ce51456d81238c4bfde4fb543dc7) | 3 → 4 |
| 320 | [Sample-Aspect Double-Descent Diagnostic](http://127.0.0.1:8848/#/problems/sample-aspect-double-descent-diagnostic) | locally_defined_component_of_unverified_research_task | [record](https://app.notion.com/p/3d26ce51456d81809145cb3d853ac0fb) | 3 → 4 |
| 328 | [Matrix Kernel Tiling Cost Optimizer](http://127.0.0.1:8848/#/problems/matrix-kernel-tiling-cost) | local_practice_without_exact_interview_provenance | [related](https://app.notion.com/p/3e46ce51456d81f891c8ea2c3d225785) | 4 → 5 |
| 330 | [Batched Multi-Head Einsum Attention](http://127.0.0.1:8848/#/problems/batched-multihead-einsum-attention) | local_practice_without_exact_interview_provenance | [related](https://app.notion.com/p/3e76ce51456d817293fcc8122de8c39f) | 4 → 5 |
| 367 | [Implement Grouped-Query Attention](http://127.0.0.1:8848/#/problems/grouped-query-attention) | saved_datadog_report_plus_reconstructed_optional_numpy_variant | [record](https://app.notion.com/p/3cf6ce51456d81dbb7d2de28cb951c6b); [related](https://app.notion.com/p/35c6ce51456d815bb26adbdb21a7cce2) | 4 → 4 |
| 389 | [Multi-Head Attention with a KV Cache](http://127.0.0.1:8848/#/problems/pytorch-multihead-kv-cache) | user_created_playground_educational_exercise | [related](https://app.notion.com/p/35c6ce51456d815bb26adbdb21a7cce2) | 3 → 3 |
| 391 | [Batched Sigmoid–ReLU Network Forward Pass](http://127.0.0.1:8848/#/problems/numpy-sigmoid-relu-network) | user_created_playground_educational_exercise | No exact page recovered | 2 → 2 |
| 394 | [Sample-Wise Double-Descent Experiment](http://127.0.0.1:8848/#/problems/sample-wise-double-descent-experiment) | runnable_reconstruction_of_unverified_research_task | [record](https://app.notion.com/p/3d26ce51456d81809145cb3d853ac0fb) | 4 → 4 |

## Correctness fixes

- Posterior inference returns the original prior for rows with no reports even when temperature differs from one.
- Matrix-chain backward initializes the left identity using the first factor row dimension, allowing rectangular compatible factors.
- Masked batched gather fills an all-padding selection from an empty item axis without attempting to gather index zero.

## Source and validation limits

Original gated 1Point3Acres bodies were not re-read because this environment has no user-Mac Chrome tool. Existing Notion summaries were retained with that limitation. Public candidate accounts and their linked preparation pages were treated as one source lineage where they describe the same event. Papers and official documentation contribute technical background, never interview frequency.

Related General Coding, ML Design, ML Algorithm and Behavioral/Project records do not establish the exact executable ML-coding contract. Pure CV/diffusion training tasks were not added. MNIST remains an existing educational lab outside the current review priorities; real MNIST data were not downloaded or run.

456 regression tests verified: 455 passed in the initial full run; the sole local-socket permission error passed on its isolated rerun. The revised 29-problem API check used independent temporary state and matched every prompt, company label, reference and test payload. JavaScript syntax and diff-whitespace checks passed.
