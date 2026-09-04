# Cover-photo walkthrough: teaching contract

The learner should be able to turn an ambiguous conversion goal into a measurable decision contract, derive a minimal design from its constraints, and explain what evidence would justify deployment.

The six-stage walkthrough is a teaching synthesis, not a universal interview script or an account of Airbnb's architecture. Success criteria come before architecture; later stages refine them. Learners can revisit assumptions and select a deep dive instead of treating every component as mandatory.

## Methodology sources

Reviewed on 2026-09-04:

- [Google: Understand the problem](https://developers.google.com/machine-learning/problem-framing/problem): frame the business outcome before ML, establish a simple baseline, check data viability, and connect predictions to actions. Applied here to the cover-selection decision and booking-outcome contract.
- [Hello Interview: Delivery Framework](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery): prioritize requirements, quantify meaningful constraints, estimate capacity when it changes a decision, deliver a complete high-level design, and select relevant deep dives. Applied here to the batch-versus-contextual choice and its serving implications.
- [Atlassian: Engineering interview handbook](https://www.atlassian.com/company/careers/resources/interviewing/engineering): evaluates exploration, questions, reliability, cost, and adaptation to new tradeoffs. Applied here to revisiting a design when assumptions or constraints change.

## Evidence boundary

The authoritative problem asks for eligible cover selection, exposure/outcome data, offline evaluation, online causal validation, and trust guardrails. It supplies no traffic scale, conversion definition, latency target, or model family. All such demo values are illustrative assumptions. Capacity estimates are workload estimates, not measured service benchmarks. Observational prediction quality does not establish incremental conversion impact; experiment uncertainty and data validity must govern release decisions.

The existing `interactive_demos` schema, sandbox, theme bridge, and content-height bridge remain the integration boundary. An optional source/version-checked scroll-start message lets explicit stage navigation reveal the walkthrough inside its host pane. Runtime content is self-contained and makes no network requests.
