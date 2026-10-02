# Evidence and reconstruction boundary

The [PracHub specification](https://prachub.com/coding-questions/compute-currency-conversion-via-graph-search), checked on 2026-10-02, supports both parts and associates the question with Uber MLE. It is a curated practice page, not a verified original candidate transcript. The canonical Notion source ledger was also fetched during this correction.

Part 1 preserves the consistent, directed-rate contract and its existing `solution` interface. Part 2 implements the source's explicit maximum-product **simple path** contract. The separate `best_rate` name lets both parts coexist in one submission. The Part 2 limit of 10 currencies / 20 edges is a local practice bound for exhaustive search, not a reported interview constraint. Finite products and tolerant comparisons are local evaluation conventions. Source counts and interview dates are unchanged.

## Part 1

Build an adjacency list and traverse from the source while carrying the accumulated product. A global visited set is sufficient because all valid routes to a currency have the same rate. Time and space are `O(V + E)`.

## Part 2

Explore each simple path with depth-first search. Track currencies on the current path, remove each currency when backtracking, and maximize the product when reaching the destination. Return `1.0` immediately for identical endpoints. A profitable cycle does not make this answer infinite because revisiting a currency is forbidden.

A global visited set is incorrect: a later route can reach the same currency at a better rate. Keeping only the highest product per currency is also generally incorrect: two prefixes can leave different currencies available for the rest of the path. Do not prune a prefix solely because its product is small; later rates may exceed one.

If `P` is the number of simple path prefixes explored, time is `O(V + E + P * (E + 1))` as a loose bound, since each prefix may scan outgoing edges. The number of prefixes can grow factorially in a dense graph. Auxiliary space is `O(V + E)`, including adjacency storage, the current path set, and a recursion stack of depth at most `V`. The practice bounds keep this exact search small.

## Why shortest-path advice needs qualifications

The source also discusses transforming rates with `-log`. Dijkstra requires nonnegative transformed edge weights (rates at most one). Bellman-Ford can handle negative edges and identify relevant negative cycles for an unrestricted-walk version. When a profitable cycle lies on a source-to-destination route, that unrestricted version has no finite maximum; detecting the cycle does not solve the maximum-product simple-path problem. General simple-path optimization with arbitrary positive rates is computationally hard. The runnable Part 2 uses the explicitly stated simple-path interpretation, rather than the source's broader arbitrage discussion.

## Additional source cross-check — 2026-10-02

- [Uber SDE2 candidate report](https://leetcode.com/discuss/post/6947609/uber-sde2-chances-by-anonymous_user-h4vb/) reports currency conversion followed by choosing the highest-value route when multiple routes exist. It does not specify simple paths or cycle semantics, so it supports the interview follow-up without verifying this entire runnable contract.
- [Maximum-value currency conversion](https://leetcode.com/discuss/post/497693/onsite-interview-question-maximum-value-after-currency-conversion/) explicitly describes asymmetric rates and forbids trading for the same currency twice. This closely matches Part 2, but the post does not identify Uber; it is linked as a company-unspecified variant.
- [Uber L4, Bangalore, March 2022](https://leetcode.com/discuss/post/1975772/uber-software-engineer-l4-bangalore-mar-2022-reject/) reports chained conversions and a disconnected-graph follow-up. Its example implementation creates reciprocal reverse edges, unlike this exercise's supplied-edge-only contract.

These are additional source links, not verified independent occurrences of this exact question. The bounded search did not establish an original Uber candidate transcript containing the complete two-part specification. No frequency or date metadata is inferred from these variants.
