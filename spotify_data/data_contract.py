"""Typed source loading and deterministic analytical-table construction.

The raw CSV is the source of truth. DuckDB tables created here are temporary
and are rebuilt for every runtime. Polars is used at the ingestion boundary
and for the conservative artist parser so that the schema is explicit before
SQL transformations begin.
"""

from __future__ import annotations

from pathlib import Path
import unicodedata

import duckdb
import polars as pl

RAW_COLUMNS = (
    "source_row_id",
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
)

RAW_SCHEMA: dict[str, pl.DataType] = {
    "source_row_id": pl.Int64,
    "track_id": pl.String,
    "artists": pl.String,
    "album_name": pl.String,
    "track_name": pl.String,
    "popularity": pl.Int64,
    "duration_ms": pl.Int64,
    "explicit": pl.Boolean,
    "danceability": pl.Float64,
    "energy": pl.Float64,
    "key": pl.Int64,
    "loudness": pl.Float64,
    "mode": pl.Int64,
    "speechiness": pl.Float64,
    "acousticness": pl.Float64,
    "instrumentalness": pl.Float64,
    "liveness": pl.Float64,
    "valence": pl.Float64,
    "tempo": pl.Float64,
    "time_signature": pl.Int64,
    "track_genre": pl.String,
}

IDENTIFIER_COLUMNS = ("track_id", "artists", "album_name", "track_name", "track_genre")
CANONICAL_TRACK_FIELDS = (
    "artists",
    "album_name",
    "track_name",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
)

IMPUTATION_POLICY = (
    "No imputation: tracks_raw preserves source nulls; downstream tables may "
    "exclude null identifiers for relational edges but must not invent feature values."
)


def load_tracks_raw(path: str | Path) -> pl.DataFrame:
    """Load the unchanged source with a declared schema.

    The source has an unnamed first header. It is deliberately renamed to
    ``source_row_id`` as an audit field; no source rows are dropped here.
    Empty CSV fields are interpreted as nulls, but no values are filled.
    """

    source_schema = {
        "": RAW_SCHEMA["source_row_id"],
        **{key: value for key, value in RAW_SCHEMA.items() if key != "source_row_id"},
    }
    frame = pl.read_csv(path, schema=source_schema, null_values=[""], try_parse_dates=False)
    frame = frame.rename({"": "source_row_id"})
    validate_source_schema(frame)
    return frame


def validate_source_schema(frame: pl.DataFrame) -> None:
    """Raise ``ValueError`` unless a frame matches the source contract."""

    if tuple(frame.columns) != RAW_COLUMNS:
        raise ValueError(f"Unexpected columns: {frame.columns!r}")
    if frame.schema != RAW_SCHEMA:
        raise ValueError(f"Unexpected schema: {frame.schema!r}")


def missing_identifier_counts(frame: pl.DataFrame) -> pl.DataFrame:
    """Return bounded missingness evidence for identifier-like source fields."""

    validate_source_schema(frame)
    total = frame.height
    return pl.DataFrame(
        {
            "column": list(IDENTIFIER_COLUMNS),
            "missing_count": [frame.get_column(column).null_count() for column in IDENTIFIER_COLUMNS],
            "missing_fraction": [
                frame.get_column(column).null_count() / total if total else 0.0
                for column in IDENTIFIER_COLUMNS
            ],
        }
    )


def validate_repeated_track_fields(frame: pl.DataFrame) -> pl.DataFrame:
    """Return repeated-track conflicts excluding popularity and genre.

    A null alongside a non-null value is treated as a disagreement. This keeps
    the canonical ``MIN`` reductions deterministic without silently choosing
    between contradictory source rows.
    """

    validate_source_schema(frame)
    conflicts: list[pl.DataFrame] = []
    for field in CANONICAL_TRACK_FIELDS:
        field_conflicts = (
            frame.filter(pl.col("track_id").is_not_null())
            .group_by("track_id")
            .agg(
                pl.col(field).n_unique().alias("distinct_values"),
                pl.col(field).is_null().sum().alias("null_count"),
                pl.len().alias("row_count"),
            )
            .filter(pl.col("distinct_values") > 1)
            .select(
                [
                    "track_id",
                    pl.lit(field).alias("field"),
                    "distinct_values",
                    "null_count",
                    "row_count",
                ]
            )
        )
        if field_conflicts.height:
            conflicts.append(field_conflicts)
    if not conflicts:
        return pl.DataFrame(
            schema={
                "track_id": pl.String,
                "field": pl.String,
                "distinct_values": pl.UInt32,
                "null_count": pl.UInt32,
                "row_count": pl.UInt32,
            }
        )
    return pl.concat(conflicts, how="vertical")


def parse_track_artists(frame: pl.DataFrame) -> pl.DataFrame:
    """Parse only literal semicolon-separated artist lists.

    Commas, slashes, ampersands, and other punctuation are preserved inside an
    artist label. Null track IDs/artists and blank split pieces produce no
    edge. The output grain is one distinct ``track_id`` × ``artist`` edge;
    ``artist_position`` records the first position observed in the source.
    Artist labels are Unicode-normalized with NFKC after trimming.
    """

    validate_source_schema(frame)
    parts = pl.col("artists").str.split(";")
    return (
        frame.select(["track_id", "artists"])
        .filter(pl.col("track_id").is_not_null() & pl.col("artists").is_not_null())
        .with_columns(
            _artist_parts=parts,
            _artist_positions=pl.int_ranges(0, parts.list.len()),
        )
        .explode(["_artist_parts", "_artist_positions"], empty_as_null=True)
        .rename({"_artist_parts": "artist", "_artist_positions": "artist_position"})
        .with_columns(
            pl.col("artist")
            .str.strip_chars()
            .map_elements(
                lambda value: unicodedata.normalize("NFKC", value),
                return_dtype=pl.String,
            )
        )
        .filter(pl.col("artist").is_not_null() & (pl.col("artist") != ""))
        .group_by(["track_id", "artist"], maintain_order=True)
        .agg(pl.col("artist_position").min().cast(pl.Int64))
        .select(["track_id", "artist", "artist_position"])
    )


def build_duckdb_layer(
    path: str | Path,
    connection: duckdb.DuckDBPyConnection | None = None,
) -> duckdb.DuckDBPyConnection:
    """Rebuild temporary ``tracks_raw``, ``tracks``, and edge tables.

    A supplied connection is reused; otherwise an explicit in-memory DuckDB
    connection is created. The source is read afresh on every invocation.
    """

    frame = load_tracks_raw(path)
    conflicts = validate_repeated_track_fields(frame)
    if conflicts.height:
        examples = conflicts.head(5).to_dicts()
        raise ValueError(
            "Repeated track rows disagree on canonical metadata/audio fields; "
            f"resolve the source or policy before canonicalization: {examples}"
        )
    connection = connection or duckdb.connect(":memory:")
    connection.register("_raw_source_frame", frame)
    connection.execute("CREATE OR REPLACE TEMP TABLE tracks_raw AS SELECT * FROM _raw_source_frame")
    connection.execute(
        """
        CREATE OR REPLACE TEMP TABLE track_genres AS
        SELECT DISTINCT track_id, TRIM(track_genre) AS track_genre
        FROM tracks_raw
        WHERE track_id IS NOT NULL
          AND track_genre IS NOT NULL
          AND TRIM(track_genre) <> ''
        """
    )

    artist_frame = parse_track_artists(frame)
    connection.register("_track_artists_frame", artist_frame)
    connection.execute(
        "CREATE OR REPLACE TEMP TABLE track_artists AS SELECT * FROM _track_artists_frame"
    )
    connection.execute(
        """
        CREATE OR REPLACE TEMP TABLE tracks AS
        SELECT
            track_id,
            MIN(artists) AS artists,
            MIN(album_name) AS album_name,
            MIN(track_name) AS track_name,
            MEDIAN(popularity) AS popularity,
            MIN(popularity) AS popularity_min,
            MAX(popularity) AS popularity_max,
            COUNT(popularity) AS popularity_count,
            COUNT(DISTINCT popularity) AS popularity_distinct_count,
            MAX(popularity) - MIN(popularity) AS popularity_range,
            COUNT(DISTINCT popularity) > 1 AS popularity_conflict,
            MIN(duration_ms) AS duration_ms,
            MIN(explicit) AS explicit,
            MIN(danceability) AS danceability,
            MIN(energy) AS energy,
            MIN(key) AS key,
            MIN(loudness) AS loudness,
            MIN(mode) AS mode,
            MIN(speechiness) AS speechiness,
            MIN(acousticness) AS acousticness,
            MIN(instrumentalness) AS instrumentalness,
            MIN(liveness) AS liveness,
            MIN(valence) AS valence,
            MIN(tempo) AS tempo,
            MIN(time_signature) AS time_signature,
            MIN(track_genre) AS representative_track_genre,
            COUNT(DISTINCT track_genre) AS genre_count
        FROM tracks_raw
        WHERE track_id IS NOT NULL
        GROUP BY track_id
        """
    )
    return connection
