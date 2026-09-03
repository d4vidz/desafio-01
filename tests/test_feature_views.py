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
from spotify_data.feature_views import _ppmi_from_cooccurrence
from spotify_data.notebook_ui import EvidenceStatus, NarrativeSection


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


def test_genre_matrix_preserves_explicit_empty_vocabulary():
    edges = pl.DataFrame({"track_id": ["a"], "track_genre": ["rock"]})
    matrix, vocabulary = genre_membership_matrix(edges, ["a"], vocabulary=[])
    assert vocabulary == []
    assert matrix.shape == (1, 0)


def test_ppmi_embedding_is_fold_local_and_multigenre_transform_is_average():
    edges = pl.DataFrame({"track_id": ["a", "a", "b", "c"], "track_genre": ["rock", "pop", "rock", "jazz"]})
    fitted = fit_genre_ppmi(edges, ["a", "b"], n_components=8)
    transformed = fitted.transform(edges, ["a", "c"])
    assert fitted.genres == ["pop", "rock"]
    assert transformed.height == 2
    assert transformed.filter(pl.col("track_id") == "c").select(pl.exclude("track_id")).sum_horizontal().item() == 0


def test_ppmi_formula_matches_manual_small_matrix_and_is_finite():
    edges = pl.DataFrame(
        {
            "track_id": ["a", "a", "b", "b", "c", "c"],
            "track_genre": ["rock", "pop", "rock", "pop", "rock", "jazz"],
        }
    )
    incidence, _ = genre_membership_matrix(edges, ["a", "b", "c"])
    cooc = incidence.T @ incidence
    np.fill_diagonal(cooc, 0)
    total = cooc.sum()
    expected = (cooc.sum(axis=1, keepdims=True) @ cooc.sum(axis=0, keepdims=True)) / total
    positive = (cooc > 0) & (expected > 0)
    manual = np.zeros_like(cooc, dtype=np.float64)
    manual[positive] = np.maximum(np.log(cooc[positive] / expected[positive]), 0)
    assert np.isfinite(manual).all()
    assert np.diag(manual).tolist() == [0.0] * manual.shape[0]
    np.testing.assert_allclose(_ppmi_from_cooccurrence(cooc), manual)
    fitted = fit_genre_ppmi(edges, ["a", "b", "c"], n_components=2)
    assert np.isfinite(fitted.components).all()


def test_narrative_section_requires_complete_context():
    section = NarrativeSection(
        title="Distribuição",
        question="Como os valores se distribuem?",
        population="Faixas canônicas.",
        unit="uma faixa",
        method="Resumimos a distribuição em quantis.",
        how_to_read="Valores maiores ficam à direita.",
        denominator="Todas as faixas válidas.",
        result="A mediana é 50.",
        interpretation="O centro observado está em 50.",
        use="Comparar recortes posteriores.",
        limitation="Não implica causalidade.",
        status=EvidenceStatus.PROTOTYPE,
    )
    assert section.status is EvidenceStatus.PROTOTYPE
    try:
        NarrativeSection(**{**section.__dict__, "result": ""})
    except ValueError as error:
        assert "result" in str(error)
    else:
        raise AssertionError("Expected empty narrative field to fail")


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
