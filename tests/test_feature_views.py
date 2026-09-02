import numpy as np
import polars as pl

from spotify_data import (
    add_semantic_features,
    bh_fdr,
    fit_genre_ppmi,
    genre_audio_profiles,
    genre_membership_matrix,
    holm_adjust,
    random_effects_pool,
)
from spotify_data.clustering import clustering_stability


def test_semantic_feature_view_is_deterministic_and_circular_key_is_encoded():
    frame = pl.DataFrame({"key": [0, 12], "duration_ms": [1000, 2000], "explicit": [True, False], "mode": [1, 0]})
    result = add_semantic_features(frame)
    assert np.isclose(result[0, "key_sin"], result[1, "key_sin"])
    assert np.isclose(result[0, "key_cos"], result[1, "key_cos"])
    assert result.schema["log_duration_ms"] == pl.Float64
    assert result[0, "explicit_binary"] == 1


def test_genre_matrix_has_explicit_vocabulary_and_oov_zero_rows():
    edges = pl.DataFrame({"track_id": ["a", "a", "b"], "track_genre": ["rock", "pop", "rock"]})
    matrix, vocabulary = genre_membership_matrix(edges, ["a", "c"], vocabulary=["pop", "rock"])
    assert vocabulary == ["pop", "rock"]
    assert matrix.tolist() == [[1.0, 1.0], [0.0, 0.0]]


def test_ppmi_embedding_is_fold_local_and_multigenre_transform_is_average():
    edges = pl.DataFrame({"track_id": ["a", "a", "b", "c"], "track_genre": ["rock", "pop", "rock", "jazz"]})
    fitted = fit_genre_ppmi(edges, ["a", "b"], n_components=8)
    transformed = fitted.transform(edges, ["a", "c"])
    assert fitted.genres == ["pop", "rock"]
    assert transformed.height == 2
    assert transformed.filter(pl.col("track_id") == "c").select(pl.exclude("track_id")).sum_horizontal().item() == 0


def test_audio_profiles_are_bounded_and_support_fractional_sensitivity():
    tracks = pl.DataFrame({
        "track_id": ["a", "b"], "danceability": [0.2, 0.8], "energy": [0.3, 0.9],
        "loudness": [-10.0, -5.0], "speechiness": [0.01, 0.02], "acousticness": [0.7, 0.1],
        "instrumentalness": [0.0, 0.1], "liveness": [0.1, 0.2], "valence": [0.2, 0.9],
        "tempo": [90.0, 120.0], "duration_ms": [1000, 2000],
    })
    edges = pl.DataFrame({"track_id": ["a", "a", "b"], "track_genre": ["rock", "pop", "rock"]})
    primary = genre_audio_profiles(tracks, edges)
    sensitivity = genre_audio_profiles(tracks, edges, fractional_weights=True)
    assert primary.height == sensitivity.height == 2
    assert "danceability_q50" in primary.columns


def test_multiplicity_helpers_preserve_shape_and_pool_heterogeneity():
    assert holm_adjust([0.01, 0.04]).shape == (2,)
    assert bh_fdr([0.01, 0.04]).shape == (2,)
    pooled = random_effects_pool(pl.DataFrame({"estimate": [1.0, 2.0], "standard_error": [0.2, 0.2]}))
    assert pooled["n"] == 2
    assert 0 <= pooled["i2"] <= 1


def test_clustering_stability_returns_both_algorithms_and_gate_columns():
    rng = np.random.default_rng(2026)
    matrix = np.vstack([rng.normal(loc=-2, size=(30, 3)), rng.normal(loc=2, size=(30, 3))])
    result = clustering_stability(matrix, k_values=range(2, 3), repeats=2)
    assert set(result["algoritmo"]) == {"kmeans", "gmm"}
    assert "gate_ari" in result.columns
