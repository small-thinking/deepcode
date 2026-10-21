# Normalization forward series source boundary

The catalog at main commit `098381f` had no standalone LayerNorm, BatchNorm,
or RMSNorm exercise. These three new exercises use company `General`, category
`ML Coding`, and tag `normalization-series`. They are independently solvable,
authored CPU PyTorch forward drills with a shared `(N,D)` scope, explicit
`eps=1e-5`, valid inputs, and no validation boilerplate. Their student descriptions
contain the operation contract, not provenance, derivations, or implementation code.

| Order | Slug | Scope |
| --- | --- | --- |
| I | `layer-norm-forward` | Per-row population statistics and feature affine parameters |
| II | `batch-norm-training-forward` | Per-feature batch population statistics and feature affine parameters |
| III | `rms-norm-forward` | Per-row RMS scaling, feature weight, no centering or bias |

## Interview context

Research was cross-checked separately from the authored APIs. These reports
support studying the operation; they do not establish these exact interfaces or
justify company tags or frequency metadata.

| Signal | Source | Evidence boundary |
| --- | --- | --- |
| ByteDance, 2024-05-28 | [Candidate report](https://www.nowcoder.com/discuss/623651948142620672) | Explicit LayerNorm coding in CV/algorithm internship fourth round |
| miHoYo, 2023-03-17 | [Candidate profile](https://www.nowcoder.com/users/259446603) | BatchNorm train and inference code; medium confidence because original post was not located |
| Meituan, 04-21, year not displayed | [Candidate report](https://www.nowcoder.com/feed/main/detail/a7c9d695438e428aafe1f2510c7e2389?sourceSSR=users) | Explicit RMSNorm CUDA C coding; this CPU exercise is a simplification |
| SiliconFlow, 04-13, year not displayed | [Candidate report](https://www.nowcoder.com/feed/main/detail/c4ef77e57ee74385bc00cd52c1bd5f09) | RMSNorm/block-reduce inference infrastructure signal; not this API |
| ByteDance, 2024-08-20 | [Candidate report](https://www.nowcoder.com/feed/main/detail/ef14567a048e4e3fa30cbe28eb5c59e3?sourceSSR=dynamic) | “Handwritten RMSNorm” remains ambiguous between implementation and formula |

## Technical references and deliberate limits

- [Layer Normalization](https://arxiv.org/abs/1607.06450) and
  [PyTorch LayerNorm](https://docs.pytorch.org/docs/stable/generated/torch.nn.LayerNorm.html):
  final-axis population variance with featurewise scale and shift.
- [Batch Normalization](https://arxiv.org/abs/1502.03167) and
  [PyTorch BatchNorm1d](https://docs.pytorch.org/docs/stable/generated/torch.nn.BatchNorm1d.html):
  training output uses population variance. Running variance uses a different
  estimator in PyTorch, but running state and evaluation are advanced discussion,
  outside this exercise. N=1 is allowed as a mathematical boundary and produces
  beta; PyTorch's ready-made training function rejects this case.
- [Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467) and
  [PyTorch RMSNorm](https://docs.pytorch.org/docs/stable/generated/torch.nn.RMSNorm.html):
  no centering or bias. The exercise fixes the default epsilon explicitly;
  PyTorch's RMSNorm default depends on dtype.

No CUDA kernels, custom backward pass, module/buffer lifecycle, or malformed-input
validation is required. No fourth method is inferred from the unresolved spoken
names “RSM” / “BMSNorm”. Maintainer reference solutions live under tests and are
not injected into candidate starter code.
