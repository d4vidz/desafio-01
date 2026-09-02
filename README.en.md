# Spotify track analysis

Reproducible exploratory analysis of Spotify track metadata and audio features using [Marimo](https://marimo.io/), [DuckDB](https://duckdb.org/), and [Polars](https://pola.rs/).

The project is question-led: charts and models should answer a documented question, make their grain and aggregation explicit, and state what the data cannot establish. The first pass covers data quality and missingness, distributions, relationships, genre-aware comparisons, PCA, clustering, bounded graph-derived views, and validated predictive modeling. Because the numeric features have no missing values, this version documents the decision not to impute.

## Repository layout

```text
data/raw/spotify_tracks.csv       # input CSV, added later
docs/data-contract.en.md          # source, grain, schema, and quality rules
docs/feature-roles.en.md          # v0.1 feature roles and evidence protocol
docs/contributing.en.md           # issue, chart, and merge-request workflow
docs/branching.en.md              # branches, commits, review, and main protection
docs/development.en.md            # local environment, Molab, and agent pairing
docs/ci.en.md                     # pipeline diagnosis and incident log
docs/team-next-steps.en.md        # team starting point and handoff
notebooks/                        # Marimo notebooks (.py), when added
tests/                            # focused tests, when added
pyproject.toml                   # dependencies and project tooling
```

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run marimo edit notebooks/spotify_analysis.py
```

For a non-interactive smoke run and notebook validation:

```bash
uv run marimo check notebooks/spotify_analysis.py
uv run marimo export html notebooks/spotify_analysis.py -o spotify_analysis.html --no-include-code
uv run pytest
```

The input file is expected at `data/raw/spotify_tracks.csv`. The notebook should fail with a clear missing-file error if it is not present; do not silently download, synthesize, or replace the source data.

## Data architecture

Each runtime creates an in-memory DuckDB connection and rebuilds its tables from the raw CSV. DuckDB is an ephemeral query layer: do not create, commit, cache, or depend on `.duckdb`/`.db` files. Use DuckDB for scans, joins, deduplication, window functions, and grouped SQL; return bounded results to Polars for typed feature work and charts.

The analysis uses relations with four explicit grains:

- `tracks_raw`: one row per source CSV row; duplicates are retained for auditability.
- `tracks_clean`: one cleaned source row without the exported index, used as shared input.
- `tracks`: one canonical row per `track_id`, used for track-level features, PCA, clustering, and popularity summaries.
- `track_genres`: one row per track–genre relationship, used for genre comparisons and graph-derived views.

See [docs/data-contract.en.md](docs/data-contract.en.md) for the full contract and quality policy.
The measured rationale for the ephemeral DuckDB layer is in [docs/duckdb-benchmark.md](docs/duckdb-benchmark.md).

## Visualization principles

Every chart must identify its question, unit of analysis, aggregation, and relevant caveat. Outputs should be bounded and readable in Marimo; avoid displaying full tables or raw graph objects. Genre charts must show sparse-group handling and clarify whether multi-genre tracks contribute to multiple groups. Treemaps and networks are allowed only when the hierarchy or edges represent a meaningful relationship—for example, `genre → artist → track` or an aggregated genre-overlap network.

## Contributing

Start with the existing GitLab guide questions, then open a focused issue for the concrete analysis or engineering deliverable. Link the issue to its question, grain, method, expected artifact, caveats, and definition of done. Keep exploratory claims descriptive unless a validated target and held-out evaluation support a predictive claim. Full workflow details are in [docs/contributing.en.md](docs/contributing.en.md).

Git conventions are documented in [docs/branching.en.md](docs/branching.en.md).
Environment and local/Molab usage are in [docs/development.en.md](docs/development.en.md); the operational team handoff is in [docs/team-next-steps.en.md](docs/team-next-steps.en.md).

## Current scope and next paths

The initial milestones are Foundation and contracts, Exploration/experiments and evidence selection, and Validated analysis/final narrative. Possible follow-ups include genre-overlap and artist–genre graphs, sensitivity analysis for duplicate and multi-genre policies, time-aware analysis if temporal data is added, and baseline popularity modeling with group-aware evaluation. These are hypotheses to investigate, not conclusions implied by the current CSV.
