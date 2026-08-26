# Data contract

This contract keeps the Spotify analysis reproducible and prevents accidental mixing of row grains.

## Source

The expected source is `data/raw/spotify_tracks.csv`. It is the authoritative input for each notebook run and should be preserved unchanged. The data-loading cell must use an explicit schema where practical and should report the file path, row count, column names, and inferred/declared dtypes.

The project does not persist an analytical database. At runtime, create `duckdb.connect(":memory:")`, load the CSV into temporary or session-scoped tables, and rebuild those tables after every restart. Persistent `.duckdb`, `.db`, or materialized database files are out of scope.

## Grains

| Relation | Grain | Purpose |
| --- | --- | --- |
| `tracks_raw` | one source row | audit duplicates, nulls, invalid values, and source fidelity |
| `tracks` | one row per `track_id` | track-level distributions, PCA, clustering, and popularity |
| `track_genres` | one row per `track_id` × genre | genre comparisons, overlap, and graph-derived views |

The source may contain repeated `track_id` values because a track can occur in more than one genre relationship. Never silently treat source rows as independent tracks. Any canonicalization rule must be named, deterministic, and compared with the raw counts.

## Quality checks

At minimum, report:

- missing count and percentage by column;
- exact duplicate rows and repeated `track_id` counts;
- expected numeric ranges and sentinel candidates, including zero durations or tempos;
- non-finite numeric values and parsing failures;
- cardinality changes from `tracks_raw` to `tracks` and `track_genres`;
- sparse genres and the number of multi-genre relationships.

Missing-value imputation is an analysis choice, not a source correction. Compare at least a global statistic and a track/group-aware strategy where possible, retain a missingness indicator when imputing features, and never overwrite `tracks_raw`.

## Typed boundaries

Use Polars (`pl.DataFrame`/`pl.LazyFrame`) for typed transformations, feature matrices, and bounded chart inputs. Use DuckDB SQL for relational operations and aggregations that benefit from its scan and join engine. Convert SQL results to Polars at the boundary and keep chart inputs small enough for interactive Marimo rendering.

## Interpretation limits

Popularity is an observed catalogue variable, not a causal outcome or a direct measure of listeners. PCA and clustering summarize feature geometry; they do not reveal listener segments. Genre comparisons must state the multi-genre counting rule and avoid overinterpreting sparse categories. Predictive claims require a declared target, leakage review, group/time-aware splitting when appropriate, and held-out metrics.
