# Notebook retrieval: four-function reconstruction

Reviewed 2026-10-06 for `notebook-rag-retrieval-evaluation`.

Read the user's linked [1Point3Acres notebook RAG write-up](https://www.1point3acres.com/interview/post/7100538) through the visible authenticated Chrome page. It explicitly labels three stages: embedding, retrieval, and evaluation. The retrieval section separately defines `cosine_similarity(query_vec, doc_matrix)` before showing retrieval using that helper. Our previous exercise folded cosine calculation into `retrieve_top_k` and exposed only three submission functions.

Expose cosine similarity as a separate task and organize the runnable exercise into four parts:

1. Batch document embedding.
2. Vectorized cosine similarities for one query against a document matrix.
3. Top-k retrieval using those scores and positional document selection.
4. Recall@k and MRR evaluation.

The embedding utility remains provided. The write-up is an editorial study reconstruction, not evidence that the candidate was asked four separately numbered interview questions. Its exact evaluation metrics are explicitly left open. Retain the original report and Notion links, and preserve the existing company/frequency metadata; this update does not add an interview occurrence. The prompt identifies the helper extraction, injected APIs, metric choices, deterministic ties, reset index, and empty/zero conventions as practice choices.

The reference solution now exposes the cosine helper and calls it from retrieval. Expand the catalog from four to nine checks, covering independent 3D cosine scoring with unequal magnitudes, negative/orthogonal/zero vectors, zero-query scores, unchanged inputs, a real default-top-10 cutoff over twelve rows, batch query embedding, metadata alignment, k=0, and an empty evaluation set. Existing document batching, tie ordering, k>N, and recall/MRR checks remain.

Keep existing browser drafts and code versions. A user's edited draft is not replaced by the new starter; they can add the cosine helper to their draft or use the existing Reset/History controls themselves.
