# Data contract (English translation)

The canonical version of this document is
[`data-contract.md`](data-contract.md). Keep both files synchronized
when the contract changes.

This contract keeps the Spotify analysis reproducible and prevents accidental mixing of row grains.

## Source

The expected source is `data/raw/spotify_tracks.csv`. It is the authoritative input for each run and must be preserved unchanged. The first CSV field has an empty header and is exposed as `source_row_id`, solely for source-row auditing. The typed loader declares the remaining schema in `spotify_data/data_contract.py`; it does not rely on auto-detection.

Empty CSV fields become nulls. No values are filled. `load_tracks_raw` validates names, order, and types before any transformation.

The project does not persist an analytical database. At runtime, create `duckdb.connect(":memory:")`, load the CSV into temporary or session-scoped tables, and rebuild those tables after every restart. Persistent `.duckdb`, `.db`, or materialized database files are out of scope.

## Grains

| Relation | Grain | Purpose |
| --- | --- | --- |
| `tracks_raw` | one source row | audit duplicates, nulls, invalid values, and source fidelity |
| `tracks` | one row per `track_id` | track-level distributions, PCA, clustering, and popularity |
| `track_genres` | one row per `track_id` × genre | genre comparisons, overlap, and graph-derived views |
| `track_artists` | one row per `track_id` × artist | artist–genre network and aggregations |

The source may contain repeated `track_id` values because a track can occur in more than one genre relationship. Never silently treat source rows as independent tracks. Null identifiers are reported; child relations that require them exclude those rows without inventing keys.

For each `track_id`, `tracks` uses median popularity and preserves `popularity_min`, `popularity_max`, `popularity_count`, `popularity_distinct_count`, `popularity_range`, and `popularity_conflict`. This makes deduplication observable rather than silent. Other repeated metadata/audio fields are reduced with deterministic `MIN` only after a fail-fast validation: any disagreement, including null versus non-null, stops construction. Popularity and genre are the exceptions; genre is explicitly many-to-many. The genre in `tracks` is only a representative value; genre analysis uses `track_genres`.

Artist parsing splits only on the literal `;`. Commas, slashes, ampersands, and other punctuation remain part of the artist label. Whitespace is trimmed, labels are Unicode-normalized with NFKC, empty pieces are discarded, and the first observed `artist_position` is retained. The final relation is distinct by `track_id` × artist.

## Quality checks

At minimum, report:

- missing count and percentage by column;
- exact duplicate rows and repeated `track_id` counts;
- expected numeric ranges and sentinel candidates, including zero durations or tempos;
- non-finite numeric values and parsing failures;
- cardinality changes from `tracks_raw` to `tracks` and `track_genres`;
- sparse genres and the number of multi-genre relationships.

There is no imputation in the source or canonical tables. `tracks_raw` preserves nulls; an analysis may exclude rows when an identifier is required, but must not invent feature values. The current source has no numeric missingness, so an artificial imputation experiment is out of scope. If a future source has numeric nulls, imputation must be a separate analytical decision with a missingness indicator and sensitivity analysis, never an overwrite of `tracks_raw`.

## Typed boundaries

Use Polars (`pl.DataFrame`/`pl.LazyFrame`) for explicit typed ingestion, the conservative artist parser, feature matrices, and bounded chart inputs. Use DuckDB SQL for temporary relational tables, deduplication, joins, and aggregations. Convert SQL results to Polars at the boundary and keep chart inputs small enough for interactive Marimo rendering.

## Interpretation limits

Every runtime explicitly creates `duckdb.connect(":memory:")` and rebuilds temporary tables from the CSV. No `.duckdb` file is persisted. Popularity is an observed catalogue variable, not a causal outcome or a direct measure of listeners. PCA and clustering summarize feature geometry; they do not reveal listener segments. Genre comparisons must state the multi-genre counting rule and avoid overinterpreting sparse categories. Predictive claims require a declared target, leakage review, group/time-aware splitting when appropriate, and held-out metrics.
