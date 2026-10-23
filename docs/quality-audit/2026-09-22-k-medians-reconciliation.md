# K-medians source reconciliation

Re-opened Inbyte confirms unrestricted pickup coordinates and the L1 k-median objective. The current main catalog instead prescribes a greedy-plus-swap k-medoids algorithm and restricts centers to existing riders. Existing PR #220 already corrects this mismatch, so this pass refreshes that PR rather than create a duplicate.

Keep the current canonical Notion mapping, Uber/Waymo company metadata for the separate K-means problem, and current frequency. Preserve the corrected unrestricted-coordinate exercise and semantic tests. Determinism and practical-heuristic acceptance are explicit local testing conventions; no initialization or particular heuristic is prescribed. Public curated summaries corroborate the problem family but are not independent candidate occurrences.
