# Instructions for agents

These instructions apply to every agent working in this repository. Portuguese documentation is canonical; this file is a supporting translation.

## Before editing

1. Read the issue/Task, its related specification, and [the notebook communication contract](docs/notebook-communication.en.md).
2. Confirm the grain, population, evidence status, and claim ceiling.
3. Preserve the shared data layer; do not copy cleaning, schema, or DuckDB construction into a notebook.
4. State non-goals and required tests before implementation.

## When creating or changing a notebook

- Documentation is created in the same change as the analysis or visualization.
- Every primary visualization explains its question, population, unit, intuitive method, reading instructions, denominator/sample, dynamic result, and limitation.
- Use the renderer and types from `spotify_data.notebook_ui` when available.
- Essential information stays in the primary flow and static HTML; do not depend on hover, tooltip, or accordion.
- Explicitly label `infraestrutura`, `protótipo`, `experimento_completo`, or `evidência_validada`.
- Do not turn association into causality or a prototype into a claim.

## Before handoff

- Update HTML and the manifest whenever a notebook changes.
- Run the checks required by the issue and record command, outcome, and environment.
- Provide the Luna → Sol delivery index: issues, commits, files/sections, artifacts, tests, risks, deviations, and follow-ups.
- Do not close an issue or resolve an MR discussion without acceptance criteria and human review.

Read the [spotify-marimo-notebook skill](.agents/skills/spotify-marimo-notebook/SKILL.md) for the procedure. Detailed contracts are in `docs/notebook-communication.en.md` and `docs/agent-review.en.md`.
