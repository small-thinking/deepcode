# DeepCode

DeepCode is a local-first coding challenge runner for machine learning and Python practice problems.

Think LeetCode for deep learning foundations: matrix operations, metrics, baselines, and small ML coding exercises that run against local tests. The current scope is ML coding problems. Future versions can grow into longer training tasks, dataset-backed evaluations, and LLM-as-judge review of logs or model behavior.

## Quick Start

Requirements:

- Python 3.11 or newer
- A browser

Clone the repo and start the local server:

```bash
git clone https://github.com/small-thinking/deepcode.git
cd deepcode
python3 -m deepcode --port 8000
```

Open `http://127.0.0.1:8000`.

## Use DeepCode Locally

From the browser you can:

- Browse available ML coding problems.
- Filter by category, difficulty, or search text.
- Read the prompt, starter code, example, and visible test cases.
- Write Python in the editor and run the local evaluator.

Submissions execute on your machine as short-lived Python subprocesses with a timeout and basic resource limits. This is useful for personal practice, but it is not a hardened sandbox for untrusted code.

## Local Deployment

DeepCode is a single Python server that serves the static UI and JSON API. No database, account system, or hosted backend is required.

Run on the default loopback host:

```bash
python3 -m deepcode
```

Run on a custom host and port:

```bash
python3 -m deepcode --host 127.0.0.1 --port 8000
```

The editor uses Ace Editor from jsDelivr, so syntax highlighting and editor keybindings require network access the first time the browser loads the editor asset.

## Run Tests

```bash
python3 -m unittest discover -s tests
```

## Add Problems

Problems are stored as JSON folders under `problems/`, so new ML coding questions can be added without changing backend or frontend code.

See [docs/adding-problems.md](docs/adding-problems.md) for the developer guide.
