# Ephemeral DuckDB benchmark

This benchmark informs the runtime design; it is not a general claim about all CSV workloads.

## Workload

- Input: `data/raw/spotify_tracks.csv` (19.22 MiB, 114,000 source rows).
- Environment: local Windows runtime, cold in-memory DuckDB connection.
- DuckDB path: load the CSV into a temporary in-memory table, then run catalogue summary, genre summary, genre filtering, and track-level deduplication.
- Comparison path: Polars lazy CSV scans performing equivalent operations independently.

## Observed timings

| Operation | DuckDB temporary table | Polars lazy CSV scan |
| --- | ---: | ---: |
| Load/rebuild the DuckDB table | 424-520 ms | n/a |
| Catalogue summary | 22-26 ms | 768 ms |
| Genre summary | 43-49 ms | 449 ms |
| Genre selector query | 2-4 ms | 483 ms |
| One-row-per-track deduplication | 27-33 ms | 438 ms |

The DuckDB table has a startup cost, but avoids repeated CSV scans when a Marimo session renders several related outputs. The final notebook therefore creates `duckdb.connect(":memory:")` and temporary tables once per runtime, then converts bounded query results to Polars for typed transformations and charts. No persistent database file is produced or required.
