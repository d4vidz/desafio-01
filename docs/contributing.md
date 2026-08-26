# Contributing workflow

This project is organized around the GitLab guide questions and small, reviewable deliverables.

## Before coding

1. Find the guide question that motivates the work.
2. Open or update a focused issue describing the question, grain, intended method, expected chart/table/model, and known caveats.
3. Keep unrelated exploration in a separate issue or notebook so the final story remains readable.

Useful labels follow the existing question taxonomy: `Descritiva`, `Comparativa`, `Relacional`, `Contextual`, `Exploratória`, `Explicativa`, and `Preditiva`. Use delivery labels such as `Data quality`, `Data layer`, `Visualization`, `Modeling`, `Documentation`, and `Review` when they add information. Normalize `Relacionais` to `Relacional` rather than creating a second spelling.

## Notebook and code standards

- Write Marimo notebooks as pure Python files, with small dependency-driven cells and a meaningful final expression for each rendered result.
- Do not mutate objects across cells; create new Polars frames or result objects.
- Rebuild the in-memory DuckDB layer from `data/raw/spotify_tracks.csv` on every runtime start.
- Keep `tracks_raw`, `tracks`, and `track_genres` distinct and name the grain in analysis functions and chart titles.
- Prefer typed Polars over pandas. Keep SQL in readable, testable cells or helper modules.
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

Run the relevant checks before opening a merge request:

```bash
uv sync
uv run marimo check notebooks/spotify_analysis.py
uv run python notebooks/spotify_analysis.py
uv run pytest
```

The merge request should summarize the question answered, data grain, changed outputs, validation commands, and remaining uncertainty. It should link the GitLab issue and state whether the work belongs to Foundation, General and genre analysis, or Final story. Close the issue only when the code is reproducible, the output is reviewed, and the documented definition of done is satisfied.
