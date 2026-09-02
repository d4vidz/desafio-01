# Team next steps

## Shared starting point

After the foundation MR reaches `main`, everyone starts by updating `main`, creating a short-lived branch linked to their issue, and running `uv sync --frozen`. The raw CSV remains immutable. Every notebook calls `spotify_data.build_duckdb_layer`, which rebuilds `tracks_raw`, `tracks_clean`, `tracks`, `track_genres`, and `track_artists`; do not copy cleaning into new cells or generate an alternative cleaned CSV.

## Taking ownership of a workstream

1. Choose an issue with sufficient scope and acceptance criteria; record a lead and reviewer.
2. Create `feature/<iid>-<summary>`, `experiment/<iid>-<summary>`, or another branch described in `docs/branching.en.md`.
3. Use a notebook in `notebooks/explorations/` for one question or experiment family. Shared code and data rules belong in modules rather than being duplicated across notebooks.
4. Record the question, grain, features, split, metrics, expected outputs, and caveats before interpreting results.
5. Open a Draft MR early, use `Refs #IID`, and do not close the issue before review and its definition of done.

## Current workstreams

- quality and contract: reconcile audited cleaning, ranges, popularity conflicts, and source-to-clean counts;
- EDA and statistics: distributions, genre heterogeneity, effect sizes, and multiple testing;
- musical structure: PCA, loadings, clustering stability, and genre relationships;
- modeling: popularity baselines, artist fingerprints, and group-aware splits;
- graphs: genre overlap and incremental ablations without a graph database;
- integration: select only reviewed evidence for `notebooks/spotify_analysis.py`.

A categorical-representation specification and a delivery comparing one-hot, multi-hot, and genre embeddings still need to enter the backlog. Those issues will be finalized in the next grilling; do not start a neural implementation before its objective and evaluation protocol are defined.

## Before requesting review

Run the commands in `docs/ci.en.md`, check bounded outputs, and write a conclusion that distinguishes association, contemporaneous prediction, and causality. If CI fails, record the pipeline, SHA, jobs, and first trace; a failure with no job is not evidence of broken code.
