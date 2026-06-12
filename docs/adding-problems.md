# Adding Problems

DeepCode problems are file-backed. To add a new question, create one folder under `problems/` with:

- `problem.json` for metadata, prompt text, starter code, and runtime settings
- `tests.json` for executable test snippets and expected output

## Folder Layout

Use a numeric prefix for ordering and a stable slug for URLs:

```text
problems/
  014-mean-baseline-regressor/
    problem.json
    tests.json
```

The folder name does not have to match the slug, but keeping them aligned makes review easier.

## problem.json

Example:

```json
{
  "id": "14",
  "slug": "mean-baseline-regressor",
  "title": "Mean Baseline Regressor",
  "category": "Machine Learning",
  "difficulty": "easy",
  "tags": ["baseline", "regression"],
  "prompt": "Write a function `mean_baseline(train_y, n_predictions)` that returns `n_predictions` copies of the mean target value.",
  "starter_code": "def mean_baseline(train_y, n_predictions):\n    pass\n",
  "example": {
    "input": "train_y = [1.0, 2.0, 4.0], n_predictions = 3",
    "output": "[2.3333, 2.3333, 2.3333]",
    "reasoning": "A mean baseline predicts the same average target for every row."
  },
  "environment": {
    "language": "python",
    "timeout_seconds": 2,
    "packages": [],
    "comparator": "numeric"
  },
  "references": [
    {
      "label": "scikit-learn DummyRegressor",
      "url": "https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyRegressor.html"
    }
  ],
  "evaluation": {
    "type": "ml_coding"
  },
  "created_at": "2026-06-10"
}
```

Required fields:

- `id`: Display and sort id. Numeric strings sort numerically.
- `slug`: Stable URL identifier. Users can open `/problems/<slug>`.
- `title`: Human-readable problem title.
- `category`: Broad topic such as `Linear Algebra`, `Machine Learning`, or `Metrics`.
- `difficulty`: Use `easy`, `medium`, or `hard`.
- `prompt`: The full task statement shown to the user.
- `starter_code`: Initial Python code loaded into the editor.
- `example`: A visible example with `input`, `output`, and `reasoning`.

Recommended fields:

- `tags`: Short searchable labels.
- `evaluation.type`: Evaluator backend. Omit it or use `ml_coding` for current problems.
- `environment.timeout_seconds`: Per-test timeout. Keep ML coding tasks short.
- `environment.comparator`: `exact` or `numeric`.
- `references`: Optional background links shown on the problem page. Use a list of `{ "label": "...", "url": "https://..." }` objects. URLs must be `http` or `https`.
- `created_at`: ISO date for review history.

Current limitations:

- `language` should be `python`.
- Current problems may rely on dependencies declared in `pyproject.toml`. NumPy is available by default.
- `packages` documents the packages a problem expects, but the runner does not install per-problem dependencies yet.
- The runner evaluates printed output from test snippets.

## Evaluator Types

ML coding problems should use the default evaluator:

```json
"evaluation": {
  "type": "ml_coding"
}
```

`ml_coding` expects `tests.json` to contain per-case Python snippets with
`test` and `expected_output`.

Small modeling problems should use a separate evaluator type rather than
overloading `ml_coding`:

```json
"evaluation": {
  "type": "ml_modeling"
}
```

`ml_modeling` expects each case to contain a Python `test` snippet with
assertions. The case passes when the snippet exits successfully, so it can check
object state, metrics, seeded randomness, or statistical ranges instead of
matching stdout. Modeling cases may omit `expected_output`; the evaluator shows
`All assertions pass` by default.

PyTorch modeling and debugging problems should use `ml_torch_modeling`:

```json
"evaluation": {
  "type": "ml_torch_modeling"
}
```

`ml_torch_modeling` uses the same assertion-style checks as `ml_modeling`, but
the problem metadata should list `torch` in `environment.packages`. Keep these
checks CPU-friendly: tiny tensors, seeded randomness when needed, and no long
training loops.

Modeling problems may also declare local data and artifact folders:

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

`data.path` and `artifacts.results_path` are relative to the problem folder and
may be local symbolic links into ignored workspace folders:

```text
problems/101-small-mlp/data -> ../../data/small-mlp
problems/101-small-mlp/eval-results -> ../../runs/101-small-mlp
```

The actual datasets, checkpoints, logs, API keys, and run outputs stay local and
are ignored by git. See [evaluator architecture](evaluators.md) for the extension
boundary.

## tests.json

`tests.json` must be a list. Each test is appended below the user's submitted code and run in a fresh local Python subprocess.

```json
[
  {
    "name": "three predictions",
    "input": "train_y = [1.0, 2.0, 4.0], n_predictions = 3",
    "test": "print(mean_baseline([1.0, 2.0, 4.0], 3))",
    "expected_output": "[2.3333, 2.3333, 2.3333]"
  }
]
```

Required fields for `ml_coding`:

- `test`: Python code that calls the user's function and prints the result.
- `expected_output`: The expected stdout after whitespace normalization.

Required fields for `ml_modeling`:

- `test`: Python code that exercises the user's model with assertions. A passing
  process exit means the case passed.

Required fields for `ml_torch_modeling`:

- `test`: Python code that exercises the user's PyTorch code with assertions. A
  passing process exit means the case passed.

Recommended test fields:

- `name`: A concise case name shown in results.
- `input`: A human-readable input summary shown to users.

For `ml_modeling`, use assertions directly in `test`:

```json
[
  {
    "name": "seeded top-k sampling",
    "input": "model = NGramCharModel(n=1).train(\"aaabbc\")",
    "test": "import random\nmodel = NGramCharModel(n=1).train(\"aaabbc\")\nrandom.seed(7)\nsamples = [model.sample_top_k('', k=2) for _ in range(300)]\nassert set(samples) <= {'a', 'b'}"
  }
]
```

## Comparators

Use `exact` when the expected output should match exactly after whitespace normalization:

```json
"comparator": "exact"
```

Use `numeric` for floating-point ML tasks. It preserves the output shape but allows small numeric differences:

```json
"comparator": "numeric"
```

For example, `[2.3333, 2.3333]` can match `[2.3333333333, 2.3333333333]`, but a different list length or surrounding structure will still fail.

## Authoring Checklist

1. Choose the next numeric id and a stable slug.
2. Write a prompt that states the function name, arguments, return value, and edge cases.
3. Keep starter code minimal and easy to rewrite by hand.
4. Add visible tests for the main behavior and edge cases.
5. Prefer deterministic, small examples that finish within the timeout.
6. Run the test suite:

```bash
uv run python -m unittest discover -s tests
```

7. Start the app and solve the new problem once through the browser:

```bash
uv run python -m deepcode --port 8000
```

## Good ML Coding Problem Shape

Good current-scope problems are deterministic and fast:

- Linear algebra primitives such as dot products, matrix-vector products, and normalization.
- Metrics such as accuracy, precision, recall, mean squared error, and cross entropy.
- Simple baselines such as majority-class prediction or mean regression.
- Small NumPy-backed updates such as one gradient descent step or array reshaping.
- Small PyTorch debugging tasks such as attention masks, tensor reshapes, loss
  functions, and compact module behavior.
- Data splitting, batching, token counting, padding, masking, and top-k selection.

Avoid hidden randomness, long training loops, external downloads, large datasets, and undeclared dependencies until the runner explicitly supports those evaluation modes.
