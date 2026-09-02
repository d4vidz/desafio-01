from pathlib import Path
import hashlib

import duckdb
import polars as pl

from spotify_data import (
    IMPUTATION_POLICY,
    RAW_COLUMNS,
    RAW_SCHEMA,
    build_duckdb_layer,
    load_tracks_raw,
    missing_identifier_counts,
    parse_track_artists,
    validate_repeated_track_fields,
)


CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "spotify_tracks.csv"
EXPECTED_SHA256 = "4858b1c2426a7c4f7cc580a900e6722e204015f7acde88d3c594abcb8aefccb4"


def _synthetic_raw(**overrides: list[object]) -> pl.DataFrame:
    values: dict[str, list[object]] = {
        "source_row_id": [0, 1, 2, 3],
        "track_id": ["t1", "t1", "t2", None],
        "artists": ["Alpha; Beta", "Alpha; Beta", "Solo, Jr.", "Ghost"],
        "album_name": ["A", "A", "B", "C"],
        "track_name": ["One", "One", "Two", "Missing ID"],
        "popularity": [10, 20, 30, 40],
        "duration_ms": [100, 100, 200, 300],
        "explicit": [False, False, True, False],
        "danceability": [0.1, 0.1, 0.2, 0.3],
        "energy": [0.2, 0.2, 0.3, 0.4],
        "key": [1, 1, 2, 3],
        "loudness": [-10.0, -10.0, -9.0, -8.0],
        "mode": [1, 1, 0, 1],
        "speechiness": [0.01, 0.01, 0.02, 0.03],
        "acousticness": [0.1, 0.1, 0.2, 0.3],
        "instrumentalness": [0.0, 0.0, 0.1, 0.2],
        "liveness": [0.1, 0.1, 0.2, 0.3],
        "valence": [0.1, 0.1, 0.2, 0.3],
        "tempo": [100.0, 100.0, 110.0, 120.0],
        "time_signature": [4, 4, 4, 4],
        "track_genre": ["g1", "g2", "g1", "g3"],
    }
    values.update(overrides)
    return pl.DataFrame(values, schema=RAW_SCHEMA)


def test_raw_csv_has_not_been_mutated():
    assert hashlib.sha256(CSV_PATH.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_loader_uses_explicit_schema_and_preserves_unnamed_source_index():
    frame = load_tracks_raw(CSV_PATH)
    assert tuple(frame.columns) == RAW_COLUMNS
    assert frame.schema == RAW_SCHEMA
    assert frame.get_column("source_row_id").head(3).to_list() == [0, 1, 2]


def test_dual_grain_tables_and_counts_are_reconstructible():
    connection = build_duckdb_layer(CSV_PATH)
    assert connection.execute("SELECT COUNT(*) FROM tracks_raw").fetchone()[0] == 114_000
    assert connection.execute("SELECT COUNT(*) FROM tracks").fetchone()[0] == 89_741
    assert connection.execute("SELECT COUNT(*) FROM track_genres").fetchone()[0] == 113_550
    assert connection.execute("SELECT COUNT(*) FROM track_artists").fetchone()[0] > 0
    assert connection.execute("SELECT COUNT(*) FROM tracks WHERE track_id IS NULL").fetchone()[0] == 0


def test_tracks_use_median_popularity_and_expose_conflict_fields():
    connection = build_duckdb_layer(CSV_PATH)
    row = connection.execute(
        """
        SELECT popularity, popularity_min, popularity_max, popularity_count,
               popularity_distinct_count, popularity_range, popularity_conflict
        FROM tracks
        WHERE popularity_conflict
        ORDER BY track_id
        LIMIT 1
        """
    ).fetchone()
    assert row is not None
    assert row[1] <= row[0] <= row[2]
    assert row[1] < row[2]
    assert row[3] > 1
    assert row[4] > 1
    assert row[5] == row[2] - row[1] > 0
    assert row[6] is True


def test_synthetic_conflict_uses_median_and_is_flagged():
    frame = _synthetic_raw()
    connection = duckdb.connect(":memory:")
    connection.register("synthetic_source", frame)
    connection.execute("CREATE TEMP TABLE tracks_raw AS SELECT * FROM synthetic_source")
    connection.execute(
        """
        CREATE TEMP TABLE tracks AS
        SELECT track_id, MEDIAN(popularity) AS popularity,
               MIN(popularity) AS popularity_min, MAX(popularity) AS popularity_max,
               COUNT(popularity) AS popularity_count,
               COUNT(DISTINCT popularity) AS popularity_distinct_count,
               MAX(popularity)-MIN(popularity) AS popularity_range,
               COUNT(DISTINCT popularity)>1 AS popularity_conflict
        FROM tracks_raw WHERE track_id IS NOT NULL GROUP BY track_id
        """
    )
    assert connection.execute("SELECT * FROM tracks WHERE track_id='t1'").fetchone() == (
        "t1",
        15.0,
        10,
        20,
        2,
        2,
        10,
        True,
    )


def test_duckdb_layer_fails_fast_on_canonical_metadata_conflicts(tmp_path):
    frame = _synthetic_raw(album_name=["A", "CONFLICT", "B", "C"])
    source = tmp_path / "conflicting.csv"
    frame.rename({"source_row_id": ""}).write_csv(source)
    try:
        build_duckdb_layer(source)
    except ValueError as error:
        assert "canonical metadata/audio fields" in str(error)
    else:
        raise AssertionError("Expected canonical metadata conflict to fail fast")


def test_repeated_track_conflict_report_excludes_popularity_and_genre():
    frame = _synthetic_raw(album_name=["A", "CONFLICT", "B", "C"])
    conflicts = validate_repeated_track_fields(frame)
    assert conflicts.select("field").unique().to_series().to_list() == ["album_name"]


def test_artist_parser_only_splits_semicolons_and_drops_missing_identifiers():
    parsed = parse_track_artists(
        _synthetic_raw(artists=["Alpha; Ｂｅｔａ", "Alpha;Beta", "Solo, Jr.", None])
    )
    assert parsed.select(["track_id", "artist"]).to_dicts() == [
        {"track_id": "t1", "artist": "Alpha"},
        {"track_id": "t1", "artist": "Beta"},
        {"track_id": "t2", "artist": "Solo, Jr."},
    ]
    assert parsed.filter(pl.col("artist") == "Alpha").item(0, "artist_position") == 0
    assert parsed.filter(pl.col("artist") == "Beta").item(0, "artist_position") == 1


def test_missing_identifier_report_is_explicit_and_edges_exclude_missing_ids():
    frame = _synthetic_raw(artists=["Alpha; Beta", "Alpha; Beta", "Solo, Jr.", None])
    missing = missing_identifier_counts(frame).to_dicts()
    assert {row["column"]: row["missing_count"] for row in missing} == {
        "track_id": 1,
        "artists": 1,
        "album_name": 0,
        "track_name": 0,
        "track_genre": 0,
    }
    assert parse_track_artists(frame).filter(pl.col("track_id").is_null()).height == 0


def test_no_imputation_policy_is_declared_and_raw_nulls_are_preserved():
    frame = _synthetic_raw(track_name=["One", "One", "Two", None])
    assert "No imputation" in IMPUTATION_POLICY
    assert frame.get_column("track_name").null_count() == 1
    assert load_tracks_raw(CSV_PATH).get_column("artists").null_count() == 1
