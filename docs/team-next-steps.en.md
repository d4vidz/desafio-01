# Team next steps

## Shared starting point

After the foundation MR reaches `main`, everyone starts by updating `main`, creating a short-lived branch linked to their issue, and running `uv sync --frozen`. The raw CSV remains immutable. Every notebook calls `spotify_data.build_data_layer`, which rebuilds `tracks_raw`, `tracks_clean`, `tracks`, `track_genres`, and `track_artists` and supplies the same contract report; do not copy cleaning into new cells or generate an alternative cleaned CSV.

## Taking ownership of a workstream

1. Choose an issue with sufficient scope and acceptance criteria; record a lead and reviewer.
2. Create `feature/<iid>-<summary>`, `experiment/<iid>-<summary>`, or another branch described in `docs/branching.en.md`.
3. Use the canonical notebook for the front: `data_contract_audit.py` for the contract, `explorations/popularity_associations.py` for statistical associations, `explorations/genre_representations.py` for genre representations/graphs, `explorations/musical_structure.py` for PCA/clustering, and `explorations/popularity_validation.py` for held-out models. Shared code and data rules belong in modules rather than being duplicated across notebooks.
4. Record the question, grain, features, split, metrics, expected outputs, and caveats before interpreting results.
5. Open a Draft MR early, use `Refs #IID`, and do not close the issue before review and its definition of done.

## Current workstreams

- quality and contract: reconcile audited cleaning, ranges, popularity conflicts, and source-to-clean counts;
- EDA and statistics: distributions, genre heterogeneity, effect sizes, and multiple testing;
- musical structure: PCA, loadings, clustering stability, and genre relationships;
- modeling: popularity baselines, artist fingerprints, and group-aware splits;
- graphs: genre overlap and incremental ablations without a graph database;
- integration: select only reviewed evidence for `notebooks/spotify_analysis.py`.

The categorical-representation protocol is now versioned in `docs/categorical-representation.en.md` and appears as an exploratory ladder in `genre_representations.py`. Do not start a neural implementation: the approved experiment is PPMI + TruncatedSVD, with fold-local fitting required for prediction.

## Before requesting review

Run the commands in `docs/ci.en.md`, regenerate snapshots with `uv run python scripts/render_notebooks.py`, verify `uv run python scripts/render_notebooks.py --check`, inspect bounded outputs, and write a conclusion that distinguishes association, contemporaneous prediction, and causality. If CI fails, record the pipeline, SHA, jobs, and first trace; a failure with no job is not evidence of broken code. The headless smoke run executes every notebook through a temporary HTML export; reviewable snapshots live under `artifacts/notebooks/html/`.
