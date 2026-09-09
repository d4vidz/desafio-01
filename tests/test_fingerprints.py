import numpy as np
import polars as pl
import pytest
from sklearn.preprocessing import StandardScaler

from spotify_data.fingerprints import diagnose_audio_neighbours


def _frame() -> pl.DataFrame:
    return pl.DataFrame({
        "track_id": ["a1", "a2", "b1", "c1"],
        "artists": ["A", "A", "B", "C"],
        "track_genre": ["rock", "rock", "rock", "pop"],
        "x": [0.0, 0.0, 0.01, 10.0],
        "y": [0.0, 0.0, 0.01, 10.0],
    })


def test_exact_duplicates_are_visible_before_and_removed_after():
    result = diagnose_audio_neighbours(_frame(), feature_columns=("x", "y"), max_queries=4)
    assert result.summary[0, "n_queries"] == 4
    assert result.summary[0, "before_same_artist_rate"] == 0.5
    assert result.summary[0, "after_same_artist_rate"] == 0.0
    assert result.audit.filter(pl.col("query_id") == "a1")[0, "after_neighbour_id"] == "b1"


def test_explicit_tolerance_removes_near_duplicates():
    result = diagnose_audio_neighbours(
        _frame(), feature_columns=("x", "y"), duplicate_tolerance=0.02, max_queries=4
    )
    audit = result.audit.filter(pl.col("query_id") == "a1")
    assert audit[0, "before_neighbour_id"] == "a2"
    assert audit[0, "after_neighbour_id"] == "c1"


def test_sampling_and_tie_breaking_are_deterministic():
    first = diagnose_audio_neighbours(_frame(), feature_columns=("x", "y"), max_queries=3)
    second = diagnose_audio_neighbours(_frame().reverse(), feature_columns=("x", "y"), max_queries=3)
    assert first.summary.to_dicts() == second.summary.to_dicts()
    assert first.audit.to_dicts() == second.audit.to_dicts()


def test_same_genre_restricts_candidates():
    frame = pl.DataFrame({
        "track_id": ["a_q", "b_same", "c_other"], "artists": ["Q", "S", "Q"],
        "track_genre": ["rock", "rock", "pop"], "x": [0.0, 1.0, 0.01], "y": [0.0, 1.0, 0.01],
    })
    unrestricted = diagnose_audio_neighbours(frame, feature_columns=("x", "y"), max_queries=3)
    restricted = diagnose_audio_neighbours(frame, feature_columns=("x", "y"), same_genre=True, max_queries=3)
    assert unrestricted.audit.filter(pl.col("query_id") == "a_q")[0, "before_neighbour_id"] == "c_other"
    assert restricted.audit.filter(pl.col("query_id") == "a_q")[0, "before_neighbour_id"] == "b_same"


@pytest.mark.parametrize("bad", [
    pl.DataFrame({"track_id": ["a"], "artists": ["A"], "x": [np.nan]}),
    pl.DataFrame({"track_id": ["a"], "artists": ["A"], "x": ["not numeric"]}),
])
def test_invalid_audio_input_is_rejected(bad: pl.DataFrame):
    with pytest.raises((TypeError, ValueError)):
        diagnose_audio_neighbours(bad, feature_columns=("x",))


def test_invalid_tolerance_and_missing_genre_are_rejected():
    with pytest.raises(ValueError, match="duplicate_tolerance"):
        diagnose_audio_neighbours(_frame(), feature_columns=("x",), duplicate_tolerance=-1)
    with pytest.raises(ValueError, match="Missing columns"):
        diagnose_audio_neighbours(_frame().drop("track_genre"), feature_columns=("x",), same_genre=True)
    without_genre = diagnose_audio_neighbours(
        _frame().drop("track_genre"), feature_columns=("x",), same_genre=False
    )
    assert without_genre.summary[0, "n_queries"] == 4


def test_candidate_population_is_seeded_bounded_and_canonical():
    frame = pl.DataFrame(
        {
            "track_id": [f"t{i}" for i in range(20)],
            "artists": [f"a{i % 4}" for i in range(20)],
            "x": np.arange(20, dtype=float),
        }
    )
    first = diagnose_audio_neighbours(
        frame, feature_columns=("x",), genre_column=None,
        max_queries=5, max_candidates=10, seed=9,
    )
    second = diagnose_audio_neighbours(
        frame.reverse(), feature_columns=("x",), genre_column=None,
        max_queries=5, max_candidates=10, seed=9,
    )
    assert first.audit.equals(second.audit)
    assert first.summary[0, "candidate_rows"] == 10
    assert first.summary[0, "distance_standardized"]
    with pytest.raises(ValueError, match="canonical row"):
        diagnose_audio_neighbours(
            pl.concat([frame, frame.head(1)]), feature_columns=("x",), genre_column=None
        )


def test_nearest_search_handles_features_with_very_different_scales():
    frame = pl.DataFrame(
        {
            "track_id": ["a", "b", "c"],
            "artists": ["A", "B", "C"],
            "small": [0.1, 0.2, 0.3],
            "large": [100_000.0, 200_000.0, 300_000.0],
        }
    )
    result = diagnose_audio_neighbours(
        frame,
        feature_columns=("small", "large"),
        genre_column=None,
        max_queries=3,
    )
    assert result.summary[0, "before_eligible_queries"] == 3
    assert result.audit["before_distance"].is_not_null().all()
    ordered = frame.sort(["track_id", "artists", "small", "large"])
    scaled = StandardScaler().fit_transform(ordered.select("small", "large").to_numpy())
    expected = float(np.linalg.norm(scaled[0] - scaled[1]))
    observed = result.audit.filter(pl.col("query_id") == "a")[0, "before_distance"]
    assert observed == pytest.approx(expected)
