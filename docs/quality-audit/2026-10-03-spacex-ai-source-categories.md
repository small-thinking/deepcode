# SpaceX AI question, category, and source audit — 2026-10-03

This audit revisits 41 existing SpaceX AI catalog entries. It creates no new DeepCode exercise. PR #294 introduced three exercises; its longer list also included existing questions. Five missing Notion records now map to existing exercises, not five new questions.

Classification follows the original requested task, with role and round as supporting context. An ML role does not make a CS question ML System Design, and an AI product does not make every backend design question ML System Design.

## Category corrections

| Exercise | Previous category | Corrected category | Original evidence |
|---|---|---|---|
| Streaming Window Kth | System Design | Coding | [xAI SWE onsite](https://www.1point3acres.com/interview/thread/1161376): coding follow-up on a large stream, time window, and bounded memory; exact local API is reconstructed. |
| Satellite Link Assignment | System Design | Coding | [2022 SpaceX Starlink SWE OA](https://www.1point3acres.com/interview/thread/914814): return feasible user/satellite assignments and maximize coverage. Historical SpaceX evidence is not an xAI occurrence. |
| Multiprocessing vs Multithreading | ML System Design | Coding / oral CS fundamentals | [xAI ML phone screen](https://www.1point3acres.com/interview/thread/1162858): compare mechanisms and describe a project using threads. |
| Input Field Code Review | System Design | Coding / written code review | [Secondary curated topic](https://www.1point3acres.com/interview/problems/dcef89ff-9f57-4c98-bbcf-10692b3248af); original code and candidate report remain unavailable. The asynchronous-validation scenario is local practice. |

The first two exercises now have callable APIs, reference solutions, and four visible test cases each. Satellite tests independently check geometry, frequency conflicts, capacity, and modest coverage; their thresholds are local smoke tests, not the original grader or an optimality guarantee. Written CS and code-review questions keep a response editor.

## Prompt and duplicate review

All 41 prompts were inspected. Removed prescribed composite-state representation, a literal refill formula, tokenizer optimization instructions, and sorting/locking hints from starter comments. The model-evaluation question now asks the reported ML judgment topics instead of an invented rare-failure release scenario. Background notes distinguish source wording from local APIs, assumptions, follow-ups, and tests.

Twenty-six plausible duplicate pairs were compared by task contract. No exact duplicate was confirmed. Fixed-window cost quotas, sliding-window accepted-request limits, token buckets, inbound/outbound limits, and variable-quota architecture have different operations or requested deliverables. Standard LRU, weighted LRU, and LFU likewise differ.

The closest design pair was broad xAI RAG versus Google's internal-document search agent. Direct verification of [Google's report](https://www.1point3acres.com/bbs/thread-1187428-1-1.html) confirmed agent design, cost/latency, 100,000 users, and framework discussion. Its prompt retains that emphasis; the broad xAI report establishes only RAG design. The Google variant remains separate, with its incorrect Google DeepMind attribution and stale frequency tier corrected from canonical Notion.

## Background evidence

All 41 entries now have Background links. Newly recovered first-person posts support [Twitter Spaces active time and real-time top-K](https://www.1point3acres.com/bbs/thread-1162725-1-1.html), [bounded adjustment for maximum distinct values](https://www.1point3acres.com/bbs/thread-1161483-1-1.html), and [synchronized bank-account subclassing](https://www.1point3acres.com/bbs/thread-1155473-1-1.html). Each source is recorded in Notion, fetched back, and linked from the existing DeepCode exercise. Mirrors and secondary practice cards do not add occurrences.

Seven entries still lack a recovered original candidate post: Sliding Window Rate Limiter, Nested Structure Flatten/Unflatten, GPU Node Group Testing, Dynamic Batch Inference, Fixed-Window Token Quota, Input Field Code Review, and Distributed Key-Value Store. Their Backgrounds explicitly identify secondary or unresolved provenance. Existing historical tiers are not presented as newly verified independent reports. Offline Social Insight Platform also remains a practice adaptation whose detailed archive contract is not established by the related Twitter Insight take-home report.

## Current design and ML list

The catalog uses SpaceX AI as its unified label. This list includes historical SpaceX material and clearly marked secondary-source practice; it must not be read as thirteen newly discovered or independently verified xAI interview questions.

| Category | Exercise | Evidence boundary |
|---|---|---|
| System Design | [Design an Offline Social Insight Platform](http://127.0.0.1:8848/#/problems/twitter-insight-platform) | Related SWE take-home; detailed offline archive scenario is practice. |
| System Design | [Design an Inbound and Outbound Rate-Limiting Gateway](http://127.0.0.1:8848/#/problems/inbound-outbound-rate-limiter) | Related rate-limiter implementation report; architecture contract is practice. |
| System Design | [Design a Variable Per-User Quota Service](http://127.0.0.1:8848/#/problems/variable-user-quota-service) | Source-backed variable quota design; exact architecture is practice. |
| System Design | [Design a Distributed Key-Value Store](http://127.0.0.1:8848/#/problems/distributed-kv-store) | Generated study page only; original interview unverified. |
| System Design | [Design a URL Shortening Service](http://127.0.0.1:8848/#/problems/url-shortening-service) | Source-backed URL-shortener architecture task. |
| System Design | [Design File Uploads for an AI Chat Product](http://127.0.0.1:8848/#/problems/ai-chat-file-upload-experience) | Exceptional Engineer SWE onsite whiteboard design. |
| System Design | [Design Bot and Abuse Protection for an AI Chat Product](http://127.0.0.1:8848/#/problems/grok-chat-bot-abuse-protection) | Exceptional Engineer SWE technical discussion on bots/abuse. |
| ML System Design | [Design an Agentic Long-Form Video Production Workflow](http://127.0.0.1:8848/#/problems/agentic-movie-production-workflow) | xAI ML/video and agent/RL screen; one-hour movie workflow. |
| ML System Design | [Design a Multi-Tenant Retrieval-Augmented Generation System](http://127.0.0.1:8848/#/problems/multi-tenant-rag-system) | Original xAI report names broad RAG; detailed tenant/API contract is practice. |
| ML System Design | [Model Evaluation and Debugging](http://127.0.0.1:8848/#/problems/model-evaluation-regression-diagnosis) | Historical SpaceX MLE technical phone; model evaluation and debugging. |
| ML Coding | [Data-Parallel and FSDP Matrix Multiplication](http://127.0.0.1:8848/#/problems/data-parallel-fsdp-matrix-multiplication) | Executable distributed matrix-multiplication exercise. |
| ML Coding | [Dynamic Batch Inference Scheduler](http://127.0.0.1:8848/#/problems/dynamic-batch-inference) | Curated candidate retelling; original post lineage unresolved. |
| ML Coding | [Image Patch Tensor Axis Reordering](http://127.0.0.1:8848/#/problems/image-patch-tensor-axis-reordering) | Original shared-question evidence; tensor axis-reordering coding task. |

## Validation

Canonical Notion edits were fetched back. Frequency snapshots stayed private; only stars and stable record IDs are committed. Focused evaluator checks, the complete repository suite, API category/source checks, and browser rendering are validated before publication. Personal practice data and stable exercise URLs are preserved.
