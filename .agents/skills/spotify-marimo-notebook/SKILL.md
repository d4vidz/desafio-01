---
name: spotify-marimo-notebook
description: Create, edit, or review this project's Marimo notebooks with narrative, reproducibility, and bounded-output requirements built in from the start.
metadata:
  short-description: Build explainable Spotify Marimo notebooks
---

# Spotify Marimo notebook workflow

Use this skill for any notebook, chart, widget, export, or notebook review in this repository.

## Read before editing

Read the linked issue/Task and specification, then `AGENTS.md`, [the communication contract](../../../docs/notebook-communication.md), [the glossary](../../../docs/glossary.md), and [the handoff contract](../../../docs/agent-review.md) when an agent review is required.

## Implement with the narrative

- Establish population, grain, evidence status, claim ceiling, and non-goals before the visual cell.
- Reuse the shared data layer and typed Polars/DuckDB transformations; do not duplicate cleaning in a notebook.
- Use `NarrativeSection`/renderer from `spotify_data.notebook_ui` when available.
- Put question, method, how-to-read, denominator, dynamic result, interpretation, and limitation in the main flow.
- Keep essential text visible in static HTML; accordions are for supporting detail only.
- Mark every result as `infraestrutura`, `protótipo`, `experimento_completo`, or `evidência_validada`.

## Validate and hand off

Test reactivity, sparse filters, OOV/fold-local behavior when relevant, output bounds, and top-to-bottom execution. Regenerate HTML and manifest. Record exact commands and outcomes. End with the Luna → Sol delivery index: issue, fixed point, commits, paths/sections, artifacts, tests, risks, deviations, and follow-ups.

Do not promote exploratory output, make causal claims from associations, resolve MR discussions, or close issues without human acceptance.
