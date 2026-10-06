# Weighted dataset batcher source review

Reviewed 2026-10-06. The [canonical Notion question](https://app.notion.com/p/3656ce51456d80c78eadfd9d95349854) already separates source evidence from its deterministic practice reconstruction.

The [April 2026 candidate report](https://www.1point3acres.com/bbs/thread-1173464-1-1.html) and its second reply page were read through authenticated Chrome. The accessible report describes a supplied DataRegistry and dataset iterators, an offset follow-up, deterministic save/resume, and removing a divisibility assumption in the final stage. It warns that earlier descriptions do not exactly match its interview. Replies clarify that the sampling helper was supplied and candidate-written tests were used. No complete original handout or algorithm is present.

The candidate links an [earlier October 2025 report](https://www.1point3acres.com/bbs/thread-1148586-1-1.html). Its relevant section is explicitly points-gated; the Background retains the source pointer without reproducing that section. This source is not used to claim an exact algorithm or add an interview-frequency signal. Both reply pages were inspected for further clarification, without recovering the missing complete interface.

DeepCode retains its executable in-memory sequence interface and explicitly chosen deterministic weighted cycle. Global-item offset, cyclic exhaustion, and checkpoint representation remain practice conventions. The prompt now follows the three-stage progression, asks about a registry/iterator adaptation, and requires a stable checkpoint that reproduces several subsequent batches. These choices do not establish the original interviewer's exact contract.

Added tests cover divisible batches, three datasets and mapping order, selected-dataset subsets, offsets inside a cycle after wraps, stable checkpoint snapshots, restoring into an already-advanced instance, structured examples, independent instances, and initial checkpoints. Existing non-divisible and invalid-constructor tests remain. Original source links and the Notion reconstruction are visible together in Background; frequency metadata is unchanged.
