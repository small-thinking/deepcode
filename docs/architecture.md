# DeepCode Architecture

![DeepCode local architecture](assets/deepcode-local-architecture.png)

This chart captures the intended system boundary: ML coding problems and small
modeling checks run through separate local evaluator paths, while larger
dataset-backed training tasks can expand the modeling path later.

## Maintainer Diagram

```mermaid
flowchart LR
    Frontend["Frontend\nProblems, editor, run results, theme UI"]
    Backend["Backend API\nProblemStore, Run API, Evaluator Registry, Static Assets"]
    Coding["ML Coding Evaluator\nPer-case tests, timeouts, comparators, sandboxed Python"]
    Modeling["ML Modeling Evaluator\nAssertion checks, optional data path, run directory, future LLM judge"]
    State["Local Project State\nproblems/, frontend/, deepcode/, data/ ignored, runs/ ignored, .env.local"]
    Optional["Optional Services\nW&B, TensorBoard, LLM API"]

    Frontend --> Backend
    Backend --> Coding
    Coding --> Frontend
    Backend --> Modeling
    Modeling -.-> Optional
    Backend --> State
    Coding --> State
    Modeling --> State
```

## Boundaries

- `frontend/` owns the browser experience.
- `deepcode/` owns the server, API routing, problem loading, and evaluator dispatch.
- `problems/` owns committed problem metadata and visible tests.
- `data/`, `runs/`, and `.env.local` are local-only and ignored by git.
- Future modeling evaluators should write metrics, logs, checkpoints, and judge inputs to local run folders unless an optional service is explicitly configured.
