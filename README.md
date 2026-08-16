# DeepCode

DeepCode is a local-first coding challenge runner for machine learning and Python practice problems.

Think LeetCode for deep learning foundations: matrix operations, metrics, baselines, small ML coding exercises, and lightweight modeling tasks that run against local checks. Future versions can grow into longer training tasks, dataset-backed evaluations, and LLM-as-judge review of logs or model behavior.

## Quick Start

Requirements:

- `uv`
- A browser

Clone the repo and start the local server:

```bash
git clone https://github.com/small-thinking/deepcode.git
cd deepcode
./scripts/setup.sh
uv run python -m deepcode --port 8848
```

Open `http://127.0.0.1:8848`.

For development with automatic restart on source, UI, or problem changes:

```bash
uv run --with watchfiles scripts/dev.py
```

The `--with watchfiles` option lets uv run the watcher without adding it to the
project dependencies. The restarted app process runs inside the same uv project
environment.

## Use DeepCode Locally

From the browser you can:

- Browse available ML coding and lightweight modeling problems.
- Browse source-backed Company Hub profiles with company links, hiring pages, stage and funding context, interview-process signals, and linked practice questions.
- Open the PyTorch Playground for free-form Python and PyTorch experiments,
  with an auto-saved draft, named browser-local sessions, Save for code or name
  updates, Save as new for copies, and a stdout/stderr console.
- Filter by category, difficulty, or search text.
- Read the prompt, starter code, example, and visible test cases.
- Write Python in the editor and run the local evaluator.
- Add local-only custom tests for ML coding problems when you want extra edge
  cases beyond the committed visible checks.
- Link local dataset folders for modeling tasks that declare a `data.path`.

Submissions and Playground scripts execute on your machine as short-lived Python subprocesses with a timeout and basic resource limits. Playground runs are capped at 30 seconds and their captured output is limited. This is useful for personal practice, but it is not a hardened sandbox for untrusted code.

DeepCode creates `.deepcode/user-state.json` on local startup and records personal completion status there when a submission passes. That local state is separate from the committed problem definitions and is ignored by git by default. Resetting a problem clears both the editor code and that problem's completion status.

DeepCode also stores user-authored ML coding checks in `.deepcode/custom-tests.json`.
These custom tests are local practice aids: they do not modify committed
`problems/*/tests.json` files and do not mark a problem complete.

## Local Deployment

DeepCode is a single Python server that serves the static UI and JSON API. No database, account system, hosted backend, or web framework is required.

Run on the default loopback host:

```bash
uv run python -m deepcode
```

Run on a custom host and port:

```bash
uv run python -m deepcode --host 127.0.0.1 --port 8848
```

The editor uses Ace Editor from jsDelivr, so syntax highlighting and editor keybindings require network access the first time the browser loads the editor asset.

## Architecture

![DeepCode local architecture](docs/assets/deepcode-local-architecture.png)

See [docs/architecture.md](docs/architecture.md) for the local system architecture chart and maintainer diagram.

## Project Layout

- `deepcode/`: backend server, API routing, problem loading, and local code runner.
- `deepcode/evaluators/`: evaluator interfaces and registered evaluation backends.
- `frontend/`: browser UI assets served by the backend.
- `problems/`: file-backed problem definitions and evaluator test cases.
- `companies/`: file-backed company research profiles linked to problem metadata.
- `.deepcode/`: local-only user state such as completed problems, ignored by git.
- `data/` and `runs/`: optional local-only folders for future dataset-backed tasks and run artifacts.
- `tests/`: backend and static UI regression tests.

## Project Environment

DeepCode uses `uv` to pin and sync the local Python environment. NumPy is included by default so ML coding problems can cover small array, metric, and optimization tasks without per-problem setup. PyTorch is included for small tensor, module, and debugging problems that run on CPU-sized examples. The lockfile keeps development and CI reproducible as more evaluation dependencies are added later.

Set up or refresh the environment:

```bash
./scripts/setup.sh
```

Equivalent direct command:

```bash
uv sync
```

The Python version is pinned in `.python-version`, and exact dependency resolution is recorded in `uv.lock`.

## Run Tests

```bash
uv run python -m unittest discover -s tests
```

## Add Problems

Problems are stored as JSON folders under `problems/`, so new ML coding and small modeling questions can be added without changing frontend code.

See [docs/adding-problems.md](docs/adding-problems.md) for the developer guide.
See [docs/evaluators.md](docs/evaluators.md) for the evaluator boundary and modeling-task extension plan.
