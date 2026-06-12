# Evaluator Architecture

DeepCode separates problem loading, API routing, and evaluation execution so the
current ML coding flow can grow into dataset-backed modeling tasks without
turning one runner into a catch-all.

## Current Flow

```text
frontend -> POST /api/problems/<slug>/run -> Evaluator Registry -> evaluator
```

The API loads a problem, creates an `EvaluationRequest`, and asks the evaluator
registry to run the evaluator named by `problem.json`:

```json
{
  "evaluation": {
    "type": "ml_coding"
  }
}
```

If a problem omits `evaluation`, it defaults to `ml_coding`.

## `ml_coding`

`ml_coding` is the current LeetCode-style evaluator. It:

- appends each test snippet below the submitted Python code
- expands leading indentation tabs to four spaces before execution
- runs every case in a fresh local subprocess
- applies a per-case timeout
- compares stdout with either `exact` or `numeric` comparison
- returns per-case pass/fail results to the browser

This evaluator is implemented in `deepcode/evaluators/ml_coding.py`. The legacy
`deepcode.runner.run_submission` import remains as a compatibility wrapper.

## `ml_modeling`

`ml_modeling` is the lightweight modeling evaluator. It is still local and
subprocess-based, but it judges each case by running assertion/check scripts
instead of comparing printed stdout. This is useful for small modeling tasks
that need behavioral checks, repeated sampling checks, or metric assertions.

Use:

```json
{
  "evaluation": {
    "type": "ml_modeling"
  }
}
```

Each `tests.json` entry must include `test`, a Python snippet appended below the
submission. The snippet should use `assert` statements and may print a short
diagnostic. A case passes when the script exits with code 0. Assertion failures,
exceptions, and timeouts are reported per case without stopping later cases.
Submitted code gets the same leading-tab indentation normalization as
`ml_coding`.

Modeling problems may also reserve local data and artifact paths:

```json
{
  "evaluation": {
    "type": "ml_modeling"
  },
  "data": {
    "path": "data",
    "required": true
  },
  "artifacts": {
    "results_path": "eval-results"
  }
}
```

`data.path` and `artifacts.results_path` are problem-relative paths. They can be
local symbolic links, for example:

```text
problems/101-small-mlp/data -> ../../data/small-mlp
problems/101-small-mlp/eval-results -> ../../runs/101-small-mlp
```

The actual `data/`, `runs/`, and local secret files are gitignored. Problem
metadata can describe the expected local layout while datasets, checkpoints,
TensorBoard logs, W&B files, and LLM judge keys stay on the user's machine.

When present, the evaluator exposes runtime paths to check scripts through:

- `DEEPCODE_PROBLEM_DIR`
- `DEEPCODE_DATA_PATH`
- `DEEPCODE_RESULTS_PATH`

For now, `ml_modeling` is intended for small local tasks that finish quickly.
Full training orchestration, TensorBoard/W&B ingestion, and LLM-as-judge can sit
behind this evaluator boundary later without changing `ml_coding`.

## `ml_torch_modeling`

`ml_torch_modeling` is the PyTorch-oriented modeling/debugging evaluator. It
uses the same assertion-style subprocess execution as `ml_modeling`, but problem
metadata can use this type to signal that the check scripts and starter code are
expected to import `torch`.

Use:

```json
{
  "evaluation": {
    "type": "ml_torch_modeling"
  },
  "environment": {
    "packages": ["torch"],
    "timeout_seconds": 10
  }
}
```

Keep torch checks small and deterministic: tiny tensors, seeded randomness when
needed, CPU execution, and short behavioral assertions. This evaluator is a good
fit for debugging attention blocks, tensor shape code, loss functions, autograd
behavior, and compact neural network modules.

Unlike the standard modeling evaluator, `ml_torch_modeling` does not apply the
default 512 MB address-space cap to child processes. PyTorch imports can exceed
that limit on Linux even for tiny CPU examples, so rely on per-case timeouts and
small deterministic checks instead.
