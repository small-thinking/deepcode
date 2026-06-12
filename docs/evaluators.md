# Evaluator Architecture

DeepCode separates problem loading, API routing, and evaluation execution so the
current ML coding flow can grow into dataset-backed modeling tasks without
turning one runner into a catch-all.

## Current Flow

```text
frontend -> POST /api/problems/<slug>/run -> Evaluator Registry -> ml_coding
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
- runs every case in a fresh local subprocess
- applies a per-case timeout
- compares stdout with either `exact` or `numeric` comparison
- returns per-case pass/fail results to the browser

This evaluator is implemented in `deepcode/evaluators/ml_coding.py`. The legacy
`deepcode.runner.run_submission` import remains as a compatibility wrapper.

## Future `ml_modeling`

Modeling tasks should use a separate evaluator type instead of expanding
`ml_coding` into training orchestration. A future modeling problem can reserve
metadata like:

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

The current API returns `501` for unregistered evaluator types. Add a modeling
evaluator by implementing the evaluator protocol and registering it in
`deepcode/evaluators/registry.py`.
