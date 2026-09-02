# Contributing workflow

This project is organized around the GitLab guide questions and small, reviewable deliverables.

## Before coding

1. Find the guide question that motivates the work.
2. Open or update a focused issue describing the question, grain, intended method, expected chart/table/model, and known caveats.
3. Keep unrelated exploration in a separate issue or notebook so the final story remains readable.

Historical labels (`Descritivas`, `Relacionais`, and so on) are preserved. For new issues, use the scoped taxonomy documented in [docs/governance.en.md](governance.en.md): one type, one workflow, and one priority label, plus the evidence and area labels that are needed. Provenance labels named `proposta::<source-or-round>` should exist only during a review round; after the decision, remove them from issues and retire them until another explicit round.

Use a `especificação` issue before implementing shared or high-risk contracts such as schema/grain, validation, headline claims, graph features, and final notebook structure. A small exploration may move directly to `entrega`. Every delivery should state its lead, reviewer, integrator when applicable, dependencies, and definition of done.

## Notebook and code standards

- Write Marimo notebooks as pure Python files, with small dependency-driven cells and a meaningful final expression for each rendered result.
- Do not mutate objects across cells; create new Polars frames or result objects.
- Rebuild the in-memory DuckDB layer from `data/raw/spotify_tracks.csv` on every runtime start.
- Keep `tracks_raw`, `tracks`, and `track_genres` distinct and name the grain in analysis functions and chart titles.
- Prefer typed Polars over pandas. Keep SQL in readable, testable cells or helper modules.
- For human analysis, use the v0.1 panel in [docs/feature-roles.en.md](feature-roles.en.md); keep the remaining features available for automated selection and sensitivity analyses.
- Do not commit database files, generated exports, notebook caches, or large unbounded chart payloads.

## Chart quality checklist

A chart is ready for review when it:

- answers a stated question;
- names the unit of analysis and aggregation;
- uses a scale and encoding that do not distort the comparison;
- handles sparse groups, duplicates, and multi-genre tracks explicitly;
- includes a concise interpretation and limitation;
- renders as a bounded Marimo output.

Treemaps require a meaningful hierarchy and additive size measure. Networks require defined nodes, edges, aggregation, and a top-*n* or filter control. A decorative category list is not a valid hierarchy or graph.

## Validation and merge requests

Use short-lived branches and merge requests as described in [docs/branching.en.md](branching.en.md). Do not push directly to `main`. Reference issues with `Refs #IID`; use closing keywords only after the definition of done is fully satisfied.

Run the relevant checks before opening a merge request:

```bash
uv sync
uv run marimo check notebooks/spotify_analysis.py
uv run marimo check notebooks/explorations/musical_structure.py
uv run marimo export html notebooks/spotify_analysis.py -o spotify_analysis.html --no-include-code
uv run pytest
```

The merge request should summarize the question answered, data grain, changed outputs, validation commands, and remaining uncertainty. It should link the GitLab issue and state whether the work belongs to Foundation and contracts, Exploration/experiments and evidence selection, or Validated analysis/final narrative. Close the issue only when the code is reproducible, the output is reviewed, and the documented definition of done is satisfied.
