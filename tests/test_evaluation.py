import polars as pl
import pytest
from polars.testing import assert_frame_equal

from spotify_data.evaluation import (
    EvaluationResult,
    EvaluationSpec,
    best_model_summary,
    evaluate_regression,
    run_evaluation,
    summarize_evaluation,
    summarize_metrics,
)


def _evaluation_frame(*, encoded_track_ids: bool = False) -> pl.DataFrame:
    rows = []
    for artist_index, artist in enumerate(("a", "b", "c", "d", "e", "f", "g", "h")):
        for track_number in range(3):
            track_id = (
                f"{artist_index * 100 + 10 * track_number + 7:03d}"
                if encoded_track_ids
                else f"{artist}-{track_number}"
            )
            rows.append(
                {
                    "track_id": track_id,
                    "primary_artist": artist,
                    "popularity": 8 * artist_index + 3 * track_number,
                    "energy": 0.1 * artist_index + 0.01 * track_number,
                    "danceability": 0.2 + 0.02 * track_number,
                }
            )
    return pl.DataFrame(rows)


def test_grouped_evaluation_never_uses_test_artists_in_training_and_is_bounded():
    rows = []
    for artist in ("a", "b", "c", "d", "e", "f"):
        for track_number in range(3):
            rows.append({
                "track_id": f"{artist}-{track_number}", "primary_artist": artist,
                "popularity": 10 + track_number, "energy": 0.2 + track_number / 10,
                "danceability": 0.3 + track_number / 10,
            })
    frame = pl.DataFrame(rows)
    results = evaluate_regression(frame, ["energy", "danceability"], repeats=2)
    assert set(results["split"].unique()) == {"artista não visto", "aleatório diagnóstico"}
    grouped = results.filter(pl.col("split") == "artista não visto")
    assert (grouped["train_artists"] + grouped["test_artists"] <= 6).all()
    summary = summarize_metrics(results)
    assert summary.height == 6
    best = best_model_summary(summary, "artista não visto")
    assert best.model in {"dummy mediana", "Ridge", "HistGradientBoosting"}
    assert isinstance(best.mae_mean, float)


def test_baseline_api_returns_only_bounded_metrics_for_all_models_and_splits():
    spec = EvaluationSpec(("energy", "danceability"), repeats=2, seed=11)

    result = run_evaluation(_evaluation_frame(), spec)

    assert isinstance(result, EvaluationResult)
    assert result.metrics.height == 2 * 2 * 3
    assert set(result.metrics["modelo"].unique()) == {
        "dummy mediana",
        "Ridge",
        "HistGradientBoosting",
    }
    assert set(result.metrics["split"].unique()) == {
        "artista não visto",
        "aleatório diagnóstico",
    }
    assert "track_id" not in result.metrics.columns
    assert "prediction" not in result.metrics.columns
    assert result.summary.height == 6


def test_track_id_is_not_a_predictor_and_is_rejected_as_a_feature():
    spec = EvaluationSpec(("energy", "danceability"), repeats=2, seed=19)

    without_id_leak = run_evaluation(_evaluation_frame(), spec).metrics
    with_id_leak = run_evaluation(
        _evaluation_frame(encoded_track_ids=True), spec
    ).metrics

    assert_frame_equal(without_id_leak, with_id_leak)
    with pytest.raises(ValueError, match="track_id"):
        EvaluationSpec(("energy", "track_id"))


def test_evaluation_rejects_duplicate_track_grain():
    frame = _evaluation_frame()
    duplicated = pl.concat([frame, frame.head(1)])
    with pytest.raises(ValueError, match="one row per track_id"):
        run_evaluation(
            duplicated, EvaluationSpec(("energy", "danceability"), repeats=1)
        )


def test_unseen_artist_split_has_disjoint_groups():
    frame = _evaluation_frame()
    result = run_evaluation(
        frame, EvaluationSpec(("energy",), repeats=3, test_size=0.25, seed=23)
    )
    grouped = result.metrics.filter(pl.col("split") == "artista não visto")

    # Every artist has three rows, so a group split must account for all eight
    # artists exactly once between train and test in every repetition.
    assert (grouped["train_artists"] + grouped["test_artists"] == 8).all()


def test_same_seed_repeats_exactly_and_different_seed_changes_the_splits():
    frame = _evaluation_frame()
    first = run_evaluation(
        frame, EvaluationSpec(("energy", "danceability"), repeats=3, seed=31)
    )
    second = run_evaluation(
        frame, EvaluationSpec(("energy", "danceability"), repeats=3, seed=31)
    )
    other_seed = run_evaluation(
        frame, EvaluationSpec(("energy", "danceability"), repeats=3, seed=32)
    )

    assert_frame_equal(first.metrics, second.metrics)
    assert not first.metrics.equals(other_seed.metrics)


def test_legacy_api_matches_new_api_and_summary_alias():
    frame = _evaluation_frame()
    spec = EvaluationSpec(("energy", "danceability"), repeats=2, seed=41)

    current = run_evaluation(frame, spec)
    legacy = evaluate_regression(
        frame, ["energy", "danceability"], repeats=2, seed=41
    )

    assert_frame_equal(current.metrics, legacy)
    assert_frame_equal(summarize_evaluation(current), summarize_metrics(legacy))
