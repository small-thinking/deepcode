# DeepCode

DeepCode is a local-first coding challenge runner for machine learning and Python practice problems. Problems live as data on disk, so you can add new questions without changing backend or frontend code.

It is built for local deployment: clone the repo, run the Python server, open the browser, and start solving.

## Run

```bash
python3 -m deepcode --port 8000
```

Open `http://127.0.0.1:8000`.

## Test

```bash
python3 -m unittest discover -s tests
```

## Frontend Shape

The UI is plain HTML, CSS, and JavaScript. It uses Ace Editor from a CDN for the coding surface, so syntax highlighting, line numbers, indentation, and editor keybindings work without adding a frontend build step. A TypeScript/Vite app would still be a reasonable next step if the UI grows into reusable components, routing, local asset bundling, or richer state management.

## Problem Folders

Each problem is a folder under `problems/`:

```text
problems/
  014-mean-baseline-regressor/
    problem.json
    tests.json
```

`problem.json` holds metadata and prompt text:

```json
{
  "id": "14",
  "slug": "mean-baseline-regressor",
  "title": "Mean Baseline Regressor",
  "category": "Machine Learning",
  "difficulty": "easy",
  "tags": ["baseline", "regression"],
  "prompt": "Write a function ...",
  "starter_code": "def mean_baseline(train_y, n_predictions):\n    pass\n",
  "example": {
    "input": "train_y = [1.0, 2.0, 4.0], n_predictions = 3",
    "output": "[2.3333, 2.3333, 2.3333]",
    "reasoning": "A mean baseline predicts the same average target."
  },
  "environment": {
    "language": "python",
    "timeout_seconds": 2,
    "packages": [],
    "comparator": "numeric"
  }
}
```

`tests.json` is a list of executable test snippets:

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

The runner supports `exact` and `numeric` comparators. `numeric` keeps the same output structure but allows small floating-point differences.

## Repository Notes

- The app has no required third-party Python dependencies.
- Ace Editor is loaded from jsDelivr, so the editor requires network access on first page load.
- Add a new problem by creating a folder under `problems/` with `problem.json` and `tests.json`.
- Generated caches, virtual environments, OS metadata, and local dependency folders are ignored by `.gitignore`.

## Local Execution Note

Submissions run as short-lived local Python subprocesses with a timeout and basic resource limits. This is enough for personal practice, but it is not a hardened security sandbox for untrusted code.
