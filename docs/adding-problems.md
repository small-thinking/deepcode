# Adding ML Coding Problems

DeepCode problems are file-backed. To add a new ML coding question, create one folder under `problems/` with:

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
- `environment.timeout_seconds`: Per-test timeout. Keep ML coding tasks short.
- `environment.comparator`: `exact` or `numeric`.
- `created_at`: ISO date for review history.

Current limitations:

- `language` should be `python`.
- `packages` is reserved for future dependency handling. Current problems should rely on the Python standard library.
- The runner evaluates printed output from test snippets.

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

Required test fields:

- `test`: Python code that calls the user's function and prints the result.
- `expected_output`: The expected stdout after whitespace normalization.

Recommended test fields:

- `name`: A concise case name shown in results.
- `input`: A human-readable input summary shown to users.

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
python3 -m unittest discover -s tests
```

7. Start the app and solve the new problem once through the browser:

```bash
python3 -m deepcode --port 8000
```

## Good ML Coding Problem Shape

Good current-scope problems are pure Python, deterministic, and fast:

- Linear algebra primitives such as dot products, matrix-vector products, and normalization.
- Metrics such as accuracy, precision, recall, mean squared error, and cross entropy.
- Simple baselines such as majority-class prediction or mean regression.
- Data splitting, batching, token counting, padding, masking, and top-k selection.

Avoid hidden randomness, long training loops, external downloads, large datasets, and dependencies until the runner explicitly supports those evaluation modes.
