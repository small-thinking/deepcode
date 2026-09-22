# Interview prompt and Background audit — 2026-09-21

Scope: all **323** catalog problems on base `777cf5e`, reviewed in three disjoint prompt batches (180 coding, 62 ML, 81 design/fundamentals/behavioral) and a separate source pass on `codex/interview-prompt-audit`. This report records the pre-publication audit and validation; GitHub PR status and the running service determine the subsequent merge and deployment state. No Notion records were changed.

## Changes

- Reworded **240** prompts, preserving required APIs, mathematical definitions, state transitions, and meaningful performance requirements. Removed implementation recipes, source-reconciliation commentary, and redundant prose. Existing concise prompts were retained.
- Updated **103** visible test files: accept assertions for input validation, reduce repetitive malformed-input permutations, and keep core correctness/boundary checks. Expected operational exceptions and explicit boolean rejection APIs remain part of their contracts.
- Validation tests use `try`/`except`/`else` so a test cannot catch its own failure assertion. Independent review of 152 changed AssertionError handlers found no such self-catching assertions; review restored the separate empty-stream entropy guard.
- Corrected one loss-curve example explanation and relaxed an unspecified post-click evaluation split from exact perfect metrics to finite valid metric ranges; expected predictions remain checked.
- Updated **91** problems with **187** Background links while preserving every existing reference. The shared renderer now displays Background for every problem, including an explicit missing-source message when the reference list is empty.
- Updated the authoring guide to keep future prompts interview-like and validation proportionate.

## Source evidence and limitations

Fetched all **289** rows/pages returned by the canonical Notion question-bank query. Source verification here means that a URL is present on a contract-matched Notion record; it does **not** mean the external post was reopened or every practice API is verbatim interview wording. Question-bank/study pages and related practice variants are labeled separately. No title-only match was treated as original-source proof.

| Source coverage | Problems |
| --- | ---: |
| Report URL verified in Notion | 122 |
| No verified source | 119 |
| Related practice variant | 14 |
| Existing source, not reverified | 20 |
| Question or study page | 12 |
| Notion only; original unavailable | 30 |
| Reading or compilation only | 6 |

The 119 unlinked problems and 30 Notion-only records still lack a verified original source. Of the Notion-only records, 24 canonical pages are blank and 6 contain no original URL. These are unresolved evidence gaps, not fabricated source attributions. Additional related, study, and existing-unverified links should not be counted as verified original reports.

## Validation

- Full repository regression: **408 tests passed** in 103.786 seconds using the existing uv environment, including API, runner, reference-solution, and frontend checks.
- Coding follow-up: **147 fixture tests passed** after the second prompt pass and test simplification.
- ML follow-up: **28 fixture tests**, **3 practice fixture tests**, and **8 final focused checks** passed, including the restored empty-stream check.
- `node --check frontend/app.js` and `git diff --check` passed. Every catalog JSON loads, every problem has a review entry, and all pre-existing references are preserved.
- Browser preview on port **8931** checked a shortened design question, a coding question with no source, and the CLIP question with an original-report link. Background, example, and metadata remain readable; existing practice state is isolated from the preview.

## Per-question review

“Retained” means the existing prompt was reviewed and kept; test and reference edits are listed separately. Detailed reasons and exact Notion record IDs are in [the audit inventory](2026-09-21-interview-prompts.json).

| Problem | Prompt | Tests | Added links | Source status |
| --- | --- | --- | ---: | --- |
| [matrix-vector-dot-product](../../problems/001-matrix-vector-dot-product/problem.json) | Revised | Updated | 0 | Reading or compilation only |
| [mean-baseline-regressor](../../problems/014-mean-baseline-regressor/problem.json) | Revised | Updated | 0 | Reading or compilation only |
| [classification-accuracy](../../problems/015-classification-accuracy/problem.json) | Revised | Updated | 0 | Reading or compilation only |
| [linear-regression-gradient-step](../../problems/016-linear-regression-gradient-step/problem.json) | Retained | Unchanged | 1 | Question or study page |
| [ngram-next-character-model](../../problems/101-ngram-next-character-model/problem.json) | Retained | Unchanged | 1 | Notion only; original unavailable |
| [source-attribution-highlighter](../../problems/102-source-attribution-highlighter/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [debug-transformer-attention](../../problems/103-debug-transformer-attention/problem.json) | Retained | Unchanged | 3 | Report URL verified in Notion |
| [streaming-logit-entropy](../../problems/104-streaming-logit-entropy/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [top-p-nucleus-sampling](../../problems/105-top-p-nucleus-sampling/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [weighted-dataset-batcher](../../problems/106-weighted-dataset-batcher/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [prefix-matrix-products](../../problems/107-prefix-matrix-products/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [mnist-torch-classifier](../../problems/108-mnist-torch-classifier/problem.json) | Retained | Unchanged | 0 | Reading or compilation only |
| [vectorized-1nn-distance-network](../../problems/109-vectorized-1nn-distance-network/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [two-layer-numpy-network](../../problems/110-two-layer-numpy-network/problem.json) | Retained | Unchanged | 2 | Report URL verified in Notion |
| [extra-tree-classifier](../../problems/111-extra-tree-classifier/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [file-duplicate-groups](../../problems/112-file-duplicate-groups/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [persistent-memo-lru-cache](../../problems/113-persistent-memo-lru-cache/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [coalescing-memory-allocator](../../problems/114-coalescing-memory-allocator/problem.json) | Retained | Unchanged | 3 | Report URL verified in Notion |
| [monster-battle-simulator](../../problems/115-monster-battle-simulator/problem.json) | Retained | Unchanged | 3 | Report URL verified in Notion |
| [glean-document-indexing-queue](../../problems/116-glean-document-indexing-queue/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [data-labeling-task-scheduler](../../problems/117-data-labeling-task-scheduler/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [resumable-list-iterator](../../problems/118-resumable-list-iterator/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [linux-cd-path-resolution](../../problems/119-linux-cd-path-resolution/problem.json) | Revised | Updated | 2 | Notion only; original unavailable |
| [spreadsheet-dependency-cycle](../../problems/120-spreadsheet-dependency-cycle/problem.json) | Retained | Unchanged | 3 | Report URL verified in Notion |
| [markdown-header-chunker](../../problems/121-markdown-header-chunker/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [bootloader-instruction-interpreter](../../problems/122-bootloader-instruction-interpreter/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [contiguous-one-blocks](../../problems/123-contiguous-one-blocks/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [infection-spread-simulation](../../problems/124-infection-spread-simulation/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [infection-spread-static-immunity](../../problems/125-infection-spread-static-immunity/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [infection-spread-recovery](../../problems/126-infection-spread-recovery/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [infection-spread-pending-death](../../problems/127-infection-spread-pending-death/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [infection-spread-optimal-burn](../../problems/128-infection-spread-optimal-burn/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [session-tracker](../../problems/129-session-tracker/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [durable-in-memory-kv-store](../../problems/130-durable-in-memory-kv-store/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [sharded-matrix-multiplication](../../problems/131-sharded-matrix-multiplication/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [versioned-social-graph](../../problems/132-versioned-social-graph/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [gpu-credit-ledger-ii](../../problems/133-gpu-credit-ledger-ii/problem.json) | Revised | Updated | 0 | Question or study page |
| [in-memory-unix-file-system](../../problems/134-in-memory-unix-file-system/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [text-editor](../../problems/135-text-editor/problem.json) | Retained | Unchanged | 0 | Existing source, not reverified |
| [same-host-async-web-crawler](../../problems/136-same-host-async-web-crawler/problem.json) | Retained | Unchanged | 0 | Existing source, not reverified |
| [stack-trace-reconstruction](../../problems/137-stack-trace-reconstruction/problem.json) | Retained | Unchanged | 0 | Existing source, not reverified |
| [recipe-manager](../../problems/138-recipe-manager/problem.json) | Retained | Unchanged | 0 | Existing source, not reverified |
| [filesystem-duplicate-finder](../../problems/139-filesystem-duplicate-finder/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [infection-spread-transition-death](../../problems/140-infection-spread-transition-death/problem.json) | Retained | Unchanged | 0 | Existing source, not reverified |
| [batched-llm-inference-service](../../problems/141-batched-llm-inference-service/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [moderator-list-hierarchy](../../problems/141-moderator-list-hierarchy/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [report-chain](../../problems/142-report-chain/problem.json) | Retained | Unchanged | 0 | Existing source, not reverified |
| [word-search-ii](../../problems/143-word-search-ii/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [merge-chat-message-windows](../../problems/144-merge-chat-message-windows/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [distributed-token-bucket-rate-limiter](../../problems/145-distributed-token-bucket-rate-limiter/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [notification-system-event-batch](../../problems/146-notification-system-event-batch/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [sliding-window-rate-limiter](../../problems/147-sliding-window-rate-limiter/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [data-parallel-fsdp-matrix-multiplication](../../problems/148-data-parallel-fsdp-matrix-multiplication/problem.json) | Revised | Updated | 0 | Existing source, not reverified |
| [nested-structure-flatten-unflatten](../../problems/149-nested-structure-flatten-unflatten/problem.json) | Revised | Updated | 0 | Existing source, not reverified |
| [parallel-merge-sort](../../problems/150-parallel-merge-sort/problem.json) | Revised | Unchanged | 0 | No verified source |
| [twitter-spaces-active-time](../../problems/151-twitter-spaces-active-time/problem.json) | Retained | Unchanged | 0 | No verified source |
| [max-distinct-after-operations](../../problems/152-max-distinct-after-operations/problem.json) | Revised | Unchanged | 0 | No verified source |
| [gpu-node-group-testing](../../problems/153-gpu-node-group-testing/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [synchronized-bank-account](../../problems/154-synchronized-bank-account/problem.json) | Revised | Unchanged | 0 | No verified source |
| [weighted-lru-cache](../../problems/155-weighted-lru-cache/problem.json) | Revised | Updated | 0 | No verified source |
| [dynamic-batch-inference](../../problems/156-dynamic-batch-inference/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [in-memory-database-ttl-backup](../../problems/157-in-memory-database-ttl-backup/problem.json) | Revised | Updated | 0 | No verified source |
| [token-limiter](../../problems/158-token-limiter/problem.json) | Retained | Unchanged | 0 | No verified source |
| [streaming-window-kth](../../problems/159-streaming-window-kth/problem.json) | Revised | Unchanged | 0 | No verified source |
| [input-field-code-review](../../problems/160-input-field-code-review/problem.json) | Revised | Unchanged | 0 | No verified source |
| [twitter-insight-platform](../../problems/161-twitter-insight-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [checkers-game-engine](../../problems/162-checkers-game-engine/problem.json) | Retained | Unchanged | 0 | No verified source |
| [radix-cache](../../problems/163-radix-cache/problem.json) | Revised | Updated | 0 | No verified source |
| [transactional-kv-store](../../problems/164-transactional-kv-store/problem.json) | Revised | Updated | 0 | No verified source |
| [inbound-outbound-rate-limiter](../../problems/166-inbound-outbound-rate-limiter/problem.json) | Revised | Unchanged | 0 | No verified source |
| [agentic-movie-production-workflow](../../problems/167-agentic-movie-production-workflow/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [variable-user-quota-service](../../problems/168-variable-user-quota-service/problem.json) | Revised | Unchanged | 2 | Question or study page |
| [multi-tenant-rag-system](../../problems/169-multi-tenant-rag-system/problem.json) | Revised | Unchanged | 0 | No verified source |
| [distributed-kv-store](../../problems/170-distributed-kv-store/problem.json) | Revised | Unchanged | 2 | Question or study page |
| [message-cooldown-logger](../../problems/171-message-cooldown-logger/problem.json) | Retained | Unchanged | 0 | No verified source |
| [post-click-logistic-baseline](../../problems/172-post-click-logistic-baseline/problem.json) | Revised | Updated | 0 | No verified source |
| [word-transformation-chain](../../problems/173-word-transformation-chain/problem.json) | Revised | Unchanged | 0 | No verified source |
| [billing-status-replay](../../problems/174-billing-status-replay/problem.json) | Retained | Unchanged | 0 | No verified source |
| [memcached-protocol-parser](../../problems/175-memcached-protocol-parser/problem.json) | Revised | Unchanged | 0 | No verified source |
| [tennis-match-scoring](../../problems/176-tennis-match-scoring/problem.json) | Retained | Unchanged | 0 | No verified source |
| [concurrent-bill-status-tracker](../../problems/177-concurrent-bill-status-tracker/problem.json) | Retained | Unchanged | 0 | No verified source |
| [tennis-game-score](../../problems/178-tennis-game-score/problem.json) | Retained | Unchanged | 0 | No verified source |
| [odd-even-linked-list](../../problems/179-odd-even-linked-list/problem.json) | Retained | Unchanged | 0 | No verified source |
| [shortest-palindrome-prefix](../../problems/180-shortest-palindrome-prefix/problem.json) | Revised | Unchanged | 0 | No verified source |
| [feature-store-platform](../../problems/181-feature-store-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [video-recommendation-platform](../../problems/182-video-recommendation-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [live-chat-platform](../../problems/183-live-chat-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [gaming-leaderboard-platform](../../problems/184-gaming-leaderboard-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [community-notification-platform](../../problems/185-community-notification-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [threaded-comment-ranking-platform](../../problems/186-threaded-comment-ranking-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [autonomous-driving-evaluation-harness](../../problems/187-autonomous-driving-evaluation-harness/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [autonomous-fleet-depot-dispatch](../../problems/188-autonomous-fleet-depot-dispatch/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [deadline-aware-transformer-serving](../../problems/189-deadline-aware-transformer-serving/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [numpy-kmeans-clustering](../../problems/191-numpy-kmeans-clustering/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [matrix-framework-debugging](../../problems/192-matrix-framework-debugging/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [trie-prefix-search](../../problems/193-trie-prefix-search/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [battleship-state-machine](../../problems/194-battleship-state-machine/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [clipped-max-pooling-locations](../../problems/195-clipped-max-pooling-locations/problem.json) | Retained | Unchanged | 1 | Notion only; original unavailable |
| [two-signal-interval-sweeper](../../problems/196-two-signal-interval-sweeper/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [schema-aware-csv-ingestion](../../problems/197-schema-aware-csv-ingestion/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [physical-maze-route-discovery](../../problems/198-physical-maze-route-discovery/problem.json) | Retained | Unchanged | 1 | Notion only; original unavailable |
| [connected-quota-grid-generator](../../problems/199-connected-quota-grid-generator/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [target-expression-builder](../../problems/200-target-expression-builder/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [nearby-almost-duplicate](../../problems/201-nearby-almost-duplicate/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [nested-suffix-repeat-decoder](../../problems/202-nested-suffix-repeat-decoder/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [minimal-infix-expression-serializer](../../problems/203-minimal-infix-expression-serializer/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [blocked-board-knight-distance](../../problems/204-blocked-board-knight-distance/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [persistent-axis-coverage](../../problems/205-persistent-axis-coverage/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [minimax-two-column-layout](../../problems/206-minimax-two-column-layout/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [sparse-monochrome-square-components](../../problems/207-sparse-monochrome-square-components/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [multi-target-shortest-distances](../../problems/208-multi-target-shortest-distances/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [directed-forest-validator](../../problems/209-directed-forest-validator/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [prefix-sum-subarray-toolkit](../../problems/210-prefix-sum-subarray-toolkit/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [minimum-command-racecar](../../problems/211-minimum-command-racecar/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [quadratic-transform-sorted-array](../../problems/212-quadratic-transform-sorted-array/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [decimal-exact-fill-min-items](../../problems/213-decimal-exact-fill-min-items/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [cyclic-linked-list-intersection](../../problems/214-cyclic-linked-list-intersection/problem.json) | Retained | Unchanged | 3 | Report URL verified in Notion |
| [query-parameter-decoder](../../problems/215-query-parameter-decoder/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [minimum-cost-bundle-cover](../../problems/216-minimum-cost-bundle-cover/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [connect-k-game-engine](../../problems/217-connect-k-game-engine/problem.json) | Revised | Updated | 0 | No verified source |
| [keyed-box-collector](../../problems/218-keyed-box-collector/problem.json) | Retained | Unchanged | 0 | No verified source |
| [reactive-sum-key-store](../../problems/219-reactive-sum-key-store/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [timestamped-account-ledger](../../problems/220-timestamped-account-ledger/problem.json) | Revised | Updated | 0 | No verified source |
| [in-memory-relational-query-engine](../../problems/221-in-memory-relational-query-engine/problem.json) | Revised | Updated | 0 | No verified source |
| [split-stay-listing-pairs](../../problems/222-split-stay-listing-pairs/problem.json) | Retained | Unchanged | 0 | No verified source |
| [terrain-water-drop-rendering](../../problems/223-terrain-water-drop-rendering/problem.json) | Retained | Unchanged | 0 | No verified source |
| [first-seen-record-deduper](../../problems/224-first-seen-record-deduper/problem.json) | Retained | Unchanged | 0 | No verified source |
| [crown-region-board-score](../../problems/225-crown-region-board-score/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [minimum-capacity-subset](../../problems/226-minimum-capacity-subset/problem.json) | Retained | Unchanged | 0 | No verified source |
| [digit-permutation-lower-bound](../../problems/227-digit-permutation-lower-bound/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [multi-article-line-formatter](../../problems/228-multi-article-line-formatter/problem.json) | Retained | Unchanged | 0 | No verified source |
| [prioritized-diff-review-workflow](../../problems/229-prioritized-diff-review-workflow/problem.json) | Retained | Unchanged | 0 | No verified source |
| [reservation-hold-booking-platform](../../problems/230-reservation-hold-booking-platform/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [durable-group-messaging-platform](../../problems/231-durable-group-messaging-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [activity-time-geo-query-platform](../../problems/232-activity-time-geo-query-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [weighted-dag-ski-score](../../problems/233-weighted-dag-ski-score/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [maximum-profit-job-scheduling](../../problems/234-maximum-profit-job-scheduling/problem.json) | Retained | Unchanged | 0 | No verified source |
| [prerequisite-installation-order](../../problems/235-prerequisite-installation-order/problem.json) | Revised | Unchanged | 0 | No verified source |
| [ordered-split-stay-plans](../../problems/236-ordered-split-stay-plans/problem.json) | Retained | Unchanged | 0 | No verified source |
| [notebook-rag-retrieval-evaluation](../../problems/237-notebook-rag-retrieval-evaluation/problem.json) | Revised | Unchanged | 0 | No verified source |
| [spreadsheet-formula-engines](../../problems/238-spreadsheet-formula-engines/problem.json) | Revised | Updated | 3 | Related practice variant |
| [blocking-db-connection-pool](../../problems/239-blocking-db-connection-pool/problem.json) | Revised | Updated | 0 | No verified source |
| [public-memo-retrieval-agent](../../problems/240-public-memo-retrieval-agent/problem.json) | Revised | Unchanged | 0 | No verified source |
| [resumable-document-vault](../../problems/241-resumable-document-vault/problem.json) | Revised | Unchanged | 0 | No verified source |
| [debug-gpt-classifier-cache](../../problems/242-debug-gpt-classifier-cache/problem.json) | Retained | Unchanged | 0 | No verified source |
| [masked-transformer-encoder-classifier](../../problems/243-masked-transformer-encoder-classifier/problem.json) | Retained | Unchanged | 0 | No verified source |
| [seq2seq-reversal-debug](../../problems/244-seq2seq-reversal-debug/problem.json) | Retained | Unchanged | 0 | No verified source |
| [batched-binary-mlp](../../problems/245-batched-binary-mlp/problem.json) | Revised | Unchanged | 0 | No verified source |
| [noisy-annotator-posterior-refactor](../../problems/246-noisy-annotator-posterior-refactor/problem.json) | Revised | Updated | 0 | No verified source |
| [grpo-response-logprob-training](../../problems/247-grpo-response-logprob-training/problem.json) | Revised | Unchanged | 2 | Question or study page |
| [autograd-matmul-chain-scan](../../problems/248-autograd-matmul-chain-scan/problem.json) | Revised | Unchanged | 0 | No verified source |
| [noisy-annotator-filtered-training](../../problems/249-noisy-annotator-filtered-training/problem.json) | Retained | Unchanged | 3 | Related practice variant |
| [linear-double-descent-sweep](../../problems/250-linear-double-descent-sweep/problem.json) | Retained | Unchanged | 0 | No verified source |
| [ml-numerics-loss-curve-toolkit](../../problems/251-ml-numerics-loss-curve-toolkit/problem.json) | Revised | Updated | 0 | No verified source |
| [robust-ab-test-analysis](../../problems/252-robust-ab-test-analysis/problem.json) | Retained | Unchanged | 0 | No verified source |
| [image-data-quality-denoising](../../problems/253-image-data-quality-denoising/problem.json) | Retained | Unchanged | 0 | No verified source |
| [multi-source-infection-metrics](../../problems/254-multi-source-infection-metrics/problem.json) | Revised | Unchanged | 0 | No verified source |
| [bounded-overlap-shard-rebalancer](../../problems/255-bounded-overlap-shard-rebalancer/problem.json) | Retained | Unchanged | 0 | No verified source |
| [closed-interval-merge](../../problems/256-closed-interval-merge/problem.json) | Revised | Unchanged | 0 | No verified source |
| [conway-grid-evolution](../../problems/257-conway-grid-evolution/problem.json) | Retained | Unchanged | 0 | No verified source |
| [event-time-gpu-credit-ledger](../../problems/258-event-time-gpu-credit-ledger/problem.json) | Retained | Unchanged | 0 | No verified source |
| [ipv4-cidr-iterator](../../problems/259-ipv4-cidr-iterator/problem.json) | Retained | Unchanged | 0 | No verified source |
| [sticky-failure-credit-accounts](../../problems/260-sticky-failure-credit-accounts/problem.json) | Retained | Unchanged | 0 | No verified source |
| [dependency-topology-analyzer](../../problems/261-dependency-topology-analyzer/problem.json) | Retained | Unchanged | 0 | No verified source |
| [adversarial-decoding-cutoff-policy](../../problems/262-adversarial-decoding-cutoff-policy/problem.json) | Retained | Unchanged | 0 | No verified source |
| [async-tree-count-protocol](../../problems/263-async-tree-count-protocol/problem.json) | Revised | Unchanged | 0 | No verified source |
| [nested-toy-type-inference](../../problems/264-nested-toy-type-inference/problem.json) | Revised | Updated | 0 | No verified source |
| [resumable-multidimensional-iterator](../../problems/265-resumable-multidimensional-iterator/problem.json) | Revised | Updated | 3 | Related practice variant |
| [modal-and-fair-modal-lock](../../problems/266-modal-and-fair-modal-lock/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [event-driven-chat-bot-refactor](../../problems/267-event-driven-chat-bot-refactor/problem.json) | Retained | Unchanged | 3 | Related practice variant |
| [length-prefixed-chunked-kv-store](../../problems/268-length-prefixed-chunked-kv-store/problem.json) | Revised | Updated | 0 | No verified source |
| [concurrent-dependency-job-scheduler](../../problems/269-concurrent-dependency-job-scheduler/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [clock-injected-timemap](../../problems/270-clock-injected-timemap/problem.json) | Retained | Unchanged | 0 | No verified source |
| [causal-message-delivery-handler](../../problems/271-causal-message-delivery-handler/problem.json) | Revised | Unchanged | 0 | No verified source |
| [authoritative-online-chess-platform](../../problems/272-authoritative-online-chess-platform/problem.json) | Revised | Unchanged | 3 | Related practice variant |
| [resumable-video-generation-scheduler](../../problems/273-resumable-video-generation-scheduler/problem.json) | Retained | Unchanged | 3 | Report URL verified in Notion |
| [payment-authorization-capture-settlement](../../problems/274-payment-authorization-capture-settlement/problem.json) | Retained | Unchanged | 3 | Report URL verified in Notion |
| [durable-webhook-delivery-platform](../../problems/275-durable-webhook-delivery-platform/problem.json) | Retained | Unchanged | 0 | No verified source |
| [multi-tenant-linear-cicd-workflow-engine](../../problems/276-multi-tenant-linear-cicd-workflow-engine/problem.json) | Retained | Unchanged | 0 | No verified source |
| [streaming-llm-playground](../../problems/277-streaming-llm-playground/problem.json) | Retained | Unchanged | 0 | No verified source |
| [multi-tenant-team-messaging-platform](../../problems/278-multi-tenant-team-messaging-platform/problem.json) | Retained | Unchanged | 0 | No verified source |
| [browser-cloud-ide-sandbox-platform](../../problems/279-browser-cloud-ide-sandbox-platform/problem.json) | Retained | Unchanged | 2 | Report URL verified in Notion |
| [ephemeral-streaming-ai-chat-app](../../problems/280-ephemeral-streaming-ai-chat-app/problem.json) | Retained | Unchanged | 0 | No verified source |
| [shared-calendar-sync-platform](../../problems/281-shared-calendar-sync-platform/problem.json) | Retained | Unchanged | 0 | No verified source |
| [unlabeled-corpus-novelty-and-object-retrieval](../../problems/282-unlabeled-corpus-novelty-and-object-retrieval/problem.json) | Revised | Unchanged | 0 | No verified source |
| [global-video-upload-streaming-platform](../../problems/283-global-video-upload-streaming-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [distributed-crossword-search-service](../../problems/284-distributed-crossword-search-service/problem.json) | Revised | Unchanged | 0 | No verified source |
| [global-poi-nearest-neighbor-platform](../../problems/285-global-poi-nearest-neighbor-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [gpu-aware-cicd-platform](../../problems/286-gpu-aware-cicd-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [translation-screen-state-architecture](../../problems/287-translation-screen-state-architecture/problem.json) | Revised | Unchanged | 0 | No verified source |
| [shard-mode-median-reducer](../../problems/288-shard-mode-median-reducer/problem.json) | Revised | Updated | 1 | Notion only; original unavailable |
| [greedy-longest-match-tokenizer](../../problems/289-greedy-longest-match-tokenizer/problem.json) | Revised | Updated | 0 | No verified source |
| [stack-snapshot-trace-builder](../../problems/290-stack-snapshot-trace-builder/problem.json) | Revised | Updated | 3 | Related practice variant |
| [dense-matmul-arithmetic-intensity](../../problems/291-dense-matmul-arithmetic-intensity/problem.json) | Revised | Updated | 0 | No verified source |
| [transfer-accept-account-ledger](../../problems/292-transfer-accept-account-ledger/problem.json) | Revised | Updated | 3 | Related practice variant |
| [snapshot-task-manager](../../problems/293-snapshot-task-manager/problem.json) | Revised | Updated | 3 | Related practice variant |
| [employee-grant-manager](../../problems/294-employee-grant-manager/problem.json) | Revised | Updated | 0 | No verified source |
| [ml-configuration-registry](../../problems/295-ml-configuration-registry/problem.json) | Revised | Updated | 0 | No verified source |
| [tool-calling-agent-session](../../problems/296-tool-calling-agent-session/problem.json) | Revised | Updated | 0 | No verified source |
| [dns-cache-resolver](../../problems/297-dns-cache-resolver/problem.json) | Revised | Unchanged | 0 | No verified source |
| [numpy-image-transformation-pipeline](../../problems/298-numpy-image-transformation-pipeline/problem.json) | Revised | Updated | 3 | Related practice variant |
| [masked-batched-gather-repair](../../problems/299-masked-batched-gather-repair/problem.json) | Revised | Updated | 0 | No verified source |
| [prompt-experiment-workbench](../../problems/300-prompt-experiment-workbench/problem.json) | Revised | Unchanged | 0 | No verified source |
| [versioned-model-rollout-control-plane](../../problems/301-versioned-model-rollout-control-plane/problem.json) | Revised | Unchanged | 0 | No verified source |
| [ml-data-contract-platform](../../problems/302-ml-data-contract-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [direct-message-delivery-platform](../../problems/303-direct-message-delivery-platform/problem.json) | Revised | Unchanged | 0 | No verified source |
| [distributed-efficiency-observability](../../problems/304-distributed-efficiency-observability/problem.json) | Revised | Unchanged | 0 | No verified source |
| [capacity-utilization-rollup](../../problems/305-capacity-utilization-rollup/problem.json) | Retained | Unchanged | 2 | Related practice variant |
| [async-retry-work-queue-crawler](../../problems/306-async-retry-work-queue-crawler/problem.json) | Revised | Updated | 0 | No verified source |
| [deterministic-pair-merge-tokenizer](../../problems/307-deterministic-pair-merge-tokenizer/problem.json) | Revised | Updated | 0 | No verified source |
| [batched-image-processor](../../problems/308-batched-image-processor/problem.json) | Revised | Updated | 0 | No verified source |
| [capacity-series-analysis](../../problems/309-capacity-series-analysis/problem.json) | Revised | Updated | 2 | Related practice variant |
| [feasible-recipe-dependency-closure](../../problems/310-feasible-recipe-dependency-closure/problem.json) | Revised | Unchanged | 0 | No verified source |
| [idempotent-token-usage-ledger](../../problems/311-idempotent-token-usage-ledger/problem.json) | Retained | Unchanged | 2 | Related practice variant |
| [stable-prompt-affinity-routing](../../problems/312-stable-prompt-affinity-routing/problem.json) | Revised | Updated | 0 | No verified source |
| [concurrent-template-registry](../../problems/313-concurrent-template-registry/problem.json) | Revised | Updated | 0 | No verified source |
| [basic-bank-ledger](../../problems/314-basic-bank-ledger/problem.json) | Revised | Updated | 3 | Related practice variant |
| [versioned-record-database](../../problems/315-versioned-record-database/problem.json) | Revised | Updated | 0 | No verified source |
| [manual-lru-cache](../../problems/316-manual-lru-cache/problem.json) | Revised | Updated | 0 | No verified source |
| [database-backup-catalog](../../problems/317-database-backup-catalog/problem.json) | Revised | Updated | 3 | Related practice variant |
| [workspace-layout-state-reducer](../../problems/318-workspace-layout-state-reducer/problem.json) | Revised | Updated | 0 | No verified source |
| [idempotent-worker-recovery](../../problems/319-idempotent-worker-recovery/problem.json) | Revised | Updated | 0 | No verified source |
| [sample-aspect-double-descent-diagnostic](../../problems/320-sample-aspect-double-descent-diagnostic/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [prioritized-task-dependency-schedule](../../problems/321-prioritized-task-dependency-schedule/problem.json) | Revised | Updated | 0 | No verified source |
| [crawl-frontier-budget-planner](../../problems/322-crawl-frontier-budget-planner/problem.json) | Revised | Updated | 0 | No verified source |
| [file-inventory-profiler](../../problems/323-file-inventory-profiler/problem.json) | Retained | Unchanged | 0 | No verified source |
| [threshold-image-components](../../problems/324-threshold-image-components/problem.json) | Revised | Unchanged | 0 | No verified source |
| [canonical-url-discovery-graph](../../problems/325-canonical-url-discovery-graph/problem.json) | Revised | Updated | 0 | No verified source |
| [object-storage-namespace](../../problems/326-object-storage-namespace/problem.json) | Revised | Updated | 0 | No verified source |
| [typed-resource-registry](../../problems/327-typed-resource-registry/problem.json) | Revised | Updated | 0 | No verified source |
| [matrix-kernel-tiling-cost](../../problems/328-matrix-kernel-tiling-cost/problem.json) | Revised | Updated | 0 | No verified source |
| [versioned-get-when-database](../../problems/329-versioned-get-when-database/problem.json) | Revised | Updated | 0 | No verified source |
| [batched-multihead-einsum-attention](../../problems/330-batched-multihead-einsum-attention/problem.json) | Revised | Unchanged | 0 | Reading or compilation only |
| [threaded-round-crawler](../../problems/331-threaded-round-crawler/problem.json) | Revised | Updated | 0 | Reading or compilation only |
| [model-weight-distribution](../../problems/332-model-weight-distribution/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [multi-region-infrastructure-provisioning](../../problems/333-multi-region-infrastructure-provisioning/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [snapshot-set-historical-reads](../../problems/334-snapshot-set-historical-reads/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [prefix-cache-state-manager](../../problems/335-prefix-cache-state-manager/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [ml-serving-metrics-review](../../problems/336-ml-serving-metrics-review/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [model-evaluation-regression-diagnosis](../../problems/337-model-evaluation-regression-diagnosis/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [rocket-engine-flight-time-ledger](../../problems/338-rocket-engine-flight-time-ledger/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [satellite-link-assignment](../../problems/339-satellite-link-assignment/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [leased-work-queue](../../problems/340-leased-work-queue/problem.json) | Revised | Updated | 3 | Report URL verified in Notion |
| [unreliable-device-dispatch](../../problems/341-unreliable-device-dispatch/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [deduplicated-image-storage](../../problems/342-deduplicated-image-storage/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [internal-document-search-agent](../../problems/343-internal-document-search-agent/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [music-recommendation-agent](../../problems/344-music-recommendation-agent/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [nested-array-list-iterator](../../problems/345-nested-array-list-iterator/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [account-contact-components](../../problems/346-account-contact-components/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [exact-target-purchase-plan](../../problems/347-exact-target-purchase-plan/problem.json) | Revised | Unchanged | 0 | Existing source, not reverified |
| [cover-photo-conversion-evaluation](../../problems/348-cover-photo-conversion-evaluation/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [listing-quality-evaluation-design](../../problems/349-listing-quality-evaluation-design/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [airbnb-motivation-reflection](../../problems/350-airbnb-motivation-reflection/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [airbnb-cross-functional-project-story](../../problems/351-airbnb-cross-functional-project-story/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [minimum-number-all-digits](../../problems/352-minimum-number-all-digits/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [find-median-large-array](../../problems/353-find-median-large-array/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [image-patch-tensor-axis-reordering](../../problems/354-image-patch-tensor-axis-reordering/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [sql-top-n-played-tracks](../../problems/355-sql-top-n-played-tracks/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [indexed-message-chunks](../../problems/356-indexed-message-chunks/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [pascal-triangle-rendering](../../problems/357-pascal-triangle-rendering/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [first-haiku-prefix-sums](../../problems/358-first-haiku-prefix-sums/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [hierarchical-page-permissions](../../problems/359-hierarchical-page-permissions/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [text-document-undo-redo](../../problems/360-text-document-undo-redo/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [online-table-maximums](../../problems/361-online-table-maximums/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [resizable-circular-deque](../../problems/362-resizable-circular-deque/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [token-budget-conversation-history](../../problems/363-token-budget-conversation-history/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [flat-image-sanitization](../../problems/364-flat-image-sanitization/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [image-prediction-retry-lru](../../problems/365-image-prediction-retry-lru/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [binary-focal-loss](../../problems/366-binary-focal-loss/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [grouped-query-attention](../../problems/367-grouped-query-attention/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [async-query-pagination](../../problems/368-async-query-pagination/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [filtered-moving-window-sums](../../problems/369-filtered-moving-window-sums/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [streaming-time-range-log-store](../../problems/370-streaming-time-range-log-store/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [diffusion-training-step-debug](../../problems/371-diffusion-training-step-debug/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [image-crop-augmentations](../../problems/372-image-crop-augmentations/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [like-system-for-brands](../../problems/373-like-system-for-brands/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [image-copyright-detection-system](../../problems/374-image-copyright-detection-system/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [out-of-core-ols-design](../../problems/375-out-of-core-ols-design/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [fleet-latency-degradation-detection](../../problems/376-fleet-latency-degradation-detection/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [vulnerability-analysis-pr-agent](../../problems/377-vulnerability-analysis-pr-agent/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [multi-item-music-description](../../problems/378-multi-item-music-description/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [sequential-playlist-recommendation](../../problems/379-sequential-playlist-recommendation/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [seven-day-user-activity-prediction](../../problems/380-seven-day-user-activity-prediction/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [multiprocessing-vs-multithreading-ml-agents](../../problems/381-multiprocessing-vs-multithreading-ml-agents/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [end-to-end-project-deep-dive](../../problems/382-end-to-end-project-deep-dive/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [longest-downhill-ski-run](../../problems/383-longest-downhill-ski-run/problem.json) | Revised | Updated | 0 | Existing source, not reverified |
| [enterprise-research-assistant-verifiable-citations](../../problems/384-enterprise-research-assistant-verifiable-citations/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [serpentine-matrix-traversal](../../problems/385-serpentine-matrix-traversal/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [minimum-listing-count-capacity](../../problems/386-minimum-listing-count-capacity/problem.json) | Revised | Unchanged | 3 | Report URL verified in Notion |
| [unit-time-deadline-reward-schedule](../../problems/387-unit-time-deadline-reward-schedule/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [pytorch-projected-multihead-attention](../../problems/388-pytorch-projected-multihead-attention/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [pytorch-multihead-kv-cache](../../problems/389-pytorch-multihead-kv-cache/problem.json) | Revised | Unchanged | 0 | No verified source |
| [pytorch-projected-grouped-query-attention](../../problems/390-pytorch-projected-grouped-query-attention/problem.json) | Revised | Unchanged | 2 | Report URL verified in Notion |
| [numpy-sigmoid-relu-network](../../problems/391-numpy-sigmoid-relu-network/problem.json) | Retained | Unchanged | 0 | No verified source |
| [airbnb-listing-search-system](../../problems/393-airbnb-listing-search-system/problem.json) | Revised | Unchanged | 1 | Notion only; original unavailable |
| [sample-wise-double-descent-experiment](../../problems/394-sample-wise-double-descent-experiment/problem.json) | Revised | Updated | 2 | Report URL verified in Notion |
| [bounded-convex-minimization](../../problems/395-bounded-convex-minimization/problem.json) | Revised | Unchanged | 0 | Question or study page |
| [longest-bounded-difference-subarray](../../problems/396-longest-bounded-difference-subarray/problem.json) | Revised | Unchanged | 0 | Question or study page |
| [robots-by-blocker-distances](../../problems/397-robots-by-blocker-distances/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [sorted-squares-and-kth-square](../../problems/398-sorted-squares-and-kth-square/problem.json) | Revised | Unchanged | 0 | Question or study page |
| [phone-keypad-combination-count](../../problems/399-phone-keypad-combination-count/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [static-and-streaming-islands](../../problems/400-static-and-streaming-islands/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [l1-k-medoids-pickup-locations](../../problems/401-l1-k-medoids-pickup-locations/problem.json) | Revised | Unchanged | 0 | Question or study page |
| [linear-logistic-regression-training](../../problems/402-linear-logistic-regression-training/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [deterministic-markov-text-generator](../../problems/403-deterministic-markov-text-generator/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [order-completion-slice-metric](../../problems/404-order-completion-slice-metric/problem.json) | Revised | Unchanged | 0 | Question or study page |
| [payment-fraud-ml-system](../../problems/405-payment-fraud-ml-system/problem.json) | Revised | Unchanged | 0 | Question or study page |
| [ml-system-conflict-resolution](../../problems/406-ml-system-conflict-resolution/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [marketplace-recommendation-eta-design](../../problems/407-marketplace-recommendation-eta-design/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [clip-symmetric-contrastive-loss](../../problems/408-clip-symmetric-contrastive-loss/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [alien-dictionary-order](../../problems/409-alien-dictionary-order/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [uber-eats-search-ml-system](../../problems/410-uber-eats-search-ml-system/problem.json) | Revised | Unchanged | 0 | Question or study page |
| [notion-extend-task-queue](../../problems/413-notion-extend-task-queue/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [notion-nested-todo-list](../../problems/414-notion-nested-todo-list/problem.json) | Revised | Updated | 0 | Report URL verified in Notion |
| [notion-calendar-search](../../problems/415-notion-calendar-search/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [string-integer-addition](../../problems/416-string-integer-addition/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [replay-buffer-debugging](../../problems/417-replay-buffer-debugging/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [iot-remote-log-collection](../../problems/418-iot-remote-log-collection/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [uber-room-progression-topk-leaderboard](../../problems/419-uber-room-progression-topk-leaderboard/problem.json) | Retained | Unchanged | 0 | Report URL verified in Notion |
| [xgboost-tree-depth](../../problems/420-xgboost-tree-depth/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [regularization-vs-weight-decay](../../problems/421-regularization-vs-weight-decay/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [dropout-at-inference](../../problems/422-dropout-at-inference/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
| [training-vs-inference](../../problems/423-training-vs-inference/problem.json) | Revised | Unchanged | 0 | Report URL verified in Notion |
