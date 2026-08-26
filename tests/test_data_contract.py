from pathlib import Path
import hashlib

import duckdb


CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "spotify_tracks.csv"
EXPECTED_SHA256 = "4858b1c2426a7c4f7cc580a900e6722e204015f7acde88d3c594abcb8aefccb4"


def test_raw_csv_has_not_been_mutated():
    assert hashlib.sha256(CSV_PATH.read_bytes()).hexdigest() == EXPECTED_SHA256


def test_raw_csv_is_present_and_has_expected_columns():
    assert CSV_PATH.exists()
    connection = duckdb.connect(":memory:")
    columns = connection.execute(
        "DESCRIBE SELECT * FROM read_csv_auto(?, sample_size=-1, nullstr='')",
        [str(CSV_PATH)],
    ).fetchall()
    names = {row[0] for row in columns}
    assert {"track_id", "popularity", "duration_ms", "track_genre"}.issubset(names)


def test_dual_grain_counts_are_reconstructible():
    connection = duckdb.connect(":memory:")
    connection.execute(
        "CREATE TEMP TABLE tracks_raw AS SELECT * FROM read_csv_auto(?, sample_size=-1, nullstr='')",
        [str(CSV_PATH)],
    )
    raw_rows, track_count, edge_count = connection.execute(
        """
        SELECT
            (SELECT count(*) FROM tracks_raw),
            (SELECT count(DISTINCT track_id) FROM tracks_raw),
            (SELECT count(*) FROM (SELECT DISTINCT track_id, track_genre FROM tracks_raw WHERE track_id IS NOT NULL AND track_genre IS NOT NULL))
        """
    ).fetchone()
    assert raw_rows == 114_000
    assert track_count == 89_741
    assert edge_count == 113_550
