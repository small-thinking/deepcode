# Evidence and reconstruction boundary

The two-argument class interface and zero-weight behavior are explicit practice conventions. Candidates choose and call their own standard-library random-number generator; no RNG callback is passed by the caller. The experimentation scenario is illustrative rather than a recovered interview story.

The linked Reddit candidate report describes weighted random generation. The linked LeetCode candidate report describes a prefix-array solution followed by replacing a library search with a handwritten search. See the linked canonical record for source lineage.

## Validation

Visible tests use only `WeightedSampler(values, weights)` and `sample()`. Exact checks cover a single positive weight, zero-weight entries, fractional weights and invalid configurations. Distribution checks use fixed seeds when the implementation uses the module-level Python generator, and deliberately broad tolerances so alternative standard-library generators are supported. These are statistical smoke checks, not a proof of randomness or independence. Tests do not patch a particular random API or require a particular output sequence.
