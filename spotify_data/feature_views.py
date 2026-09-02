"""Purpose-specific, typed feature and genre representations.

The functions here are deliberately fit/transform shaped.  A caller can fit
on a training subset and transform a held-out subset without learning a
vocabulary or embedding from held-out rows.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import polars as pl
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.preprocessing import RobustScaler

CONTINUOUS_AUDIO_FEATURES = (
    "danceability", "energy", "loudness", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence", "tempo", "duration_ms",
)
HUMAN_AUDIO_FEATURES = (
    "danceability", "energy", "valence", "acousticness", "instrumentalness", "speechiness",
)
CATEGORICAL_FEATURES = ("explicit", "key", "mode", "time_signature")


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    order = np.argsort(values)
    ordered_values = values[order]
    ordered_weights = weights[order]
    cumulative = np.cumsum(ordered_weights) / ordered_weights.sum()
    return float(np.interp(quantile, cumulative, ordered_values))


@dataclass(frozen=True)
class FeatureViewSpec:
    name: str
    numeric: tuple[str, ...]
    categorical: tuple[str, ...] = CATEGORICAL_FEATURES
    target: str = "popularity"


HUMAN_PANEL = FeatureViewSpec("human_panel_v0_1", HUMAN_AUDIO_FEATURES)
STRUCTURE_POOL = FeatureViewSpec("structure_pool_v0_1", CONTINUOUS_AUDIO_FEATURES)


def add_semantic_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Add deterministic semantic encodings; no data-dependent fitting occurs."""

    return frame.with_columns(
        (2 * math.pi * pl.col("key") / 12).sin().alias("key_sin"),
        (2 * math.pi * pl.col("key") / 12).cos().alias("key_cos"),
        pl.col("duration_ms").clip(lower_bound=1).log().alias("log_duration_ms"),
        pl.col("explicit").cast(pl.Int8).alias("explicit_binary"),
        pl.col("mode").cast(pl.Int8).alias("mode_binary"),
    )


def feature_columns(spec: FeatureViewSpec, *, include_semantic: bool = True) -> list[str]:
    columns = list(spec.numeric) + list(spec.categorical)
    if include_semantic:
        columns += ["key_sin", "key_cos", "log_duration_ms"]
    return columns


def genre_membership_matrix(
    track_genres: pl.DataFrame,
    track_ids: list[str] | np.ndarray,
    *,
    vocabulary: list[str] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Build a sparse-friendly dense multi-hot matrix with explicit OOV policy."""

    ids = [str(value) for value in track_ids]
    selected = track_genres.filter(pl.col("track_id").is_in(ids))
    vocab = vocabulary or sorted(selected.get_column("track_genre").unique().to_list())
    index = {genre: i for i, genre in enumerate(vocab)}
    matrix = np.zeros((len(ids), len(vocab)), dtype=np.float32)
    row_index = {track_id: i for i, track_id in enumerate(ids)}
    for track_id, genre in selected.iter_rows():
        if track_id in row_index and genre in index:
            matrix[row_index[track_id], index[genre]] = 1.0
    return matrix, vocab


@dataclass
class GenrePPMIEmbedding:
    genres: list[str]
    components: np.ndarray
    n_components: int
    explained_variance: float

    def transform(self, track_genres: pl.DataFrame, track_ids: list[str] | np.ndarray) -> pl.DataFrame:
        matrix = np.zeros((len(track_ids), self.n_components), dtype=np.float32)
        id_index = {str(track_id): i for i, track_id in enumerate(track_ids)}
        genre_index = {genre: i for i, genre in enumerate(self.genres)}
        counts = np.zeros(len(track_ids), dtype=np.int32)
        for track_id, genre in track_genres.iter_rows():
            row = id_index.get(str(track_id))
            col = genre_index.get(genre)
            if row is not None and col is not None:
                matrix[row] += self.components[col]
                counts[row] += 1
        valid = counts > 0
        matrix[valid] /= counts[valid, None]
        return pl.DataFrame(
            {"track_id": list(track_ids), **{f"genre_emb_{i+1}": matrix[:, i] for i in range(self.n_components)}}
        )


def fit_genre_ppmi(
    track_genres: pl.DataFrame,
    train_track_ids: list[str] | np.ndarray,
    *,
    n_components: int = 8,
) -> GenrePPMIEmbedding:
    """Fit a genre co-occurrence PPMI + SVD embedding on training tracks only."""

    incidence, genres = genre_membership_matrix(track_genres, train_track_ids)
    if not genres:
        return GenrePPMIEmbedding([], np.zeros((0, n_components), dtype=np.float32), n_components, 0.0)
    cooc = incidence.T @ incidence
    np.fill_diagonal(cooc, 0)
    total = cooc.sum()
    if total <= 0:
        return GenrePPMIEmbedding(genres, np.zeros((len(genres), n_components), dtype=np.float32), n_components, 0.0)
    row_mass = cooc.sum(axis=1, keepdims=True)
    col_mass = cooc.sum(axis=0, keepdims=True)
    expected = (row_mass @ col_mass) / total
    ratio = np.ones_like(cooc)
    positive = (cooc > 0) & (expected > 0)
    ratio[positive] = cooc[positive] * total / expected[positive]
    ppmi = np.zeros_like(cooc)
    ppmi[positive] = np.maximum(np.log(ratio[positive]), 0)
    rank = min(n_components, max(1, min(ppmi.shape) - 1))
    svd = TruncatedSVD(n_components=rank, random_state=2026)
    components = svd.fit_transform(ppmi)
    if rank < n_components:
        components = np.pad(components, ((0, 0), (0, n_components - rank)))
    return GenrePPMIEmbedding(genres, components.astype(np.float32), n_components, float(svd.explained_variance_ratio_.sum()))


def genre_audio_profiles(
    tracks: pl.DataFrame,
    track_genres: pl.DataFrame,
    *,
    quantiles: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90),
    fractional_weights: bool = False,
) -> pl.DataFrame:
    """Return bounded genre × quantile audio profiles.

    The primary view uses every genre membership equally.  ``fractional_weights``
    is a sensitivity option that gives a multigenre track total mass 1/k.
    """

    base = track_genres.join(tracks.select(["track_id", *CONTINUOUS_AUDIO_FEATURES]), on="track_id", how="inner")
    if fractional_weights:
        base = base.with_columns((1 / pl.len().over("track_id")).alias("membership_weight"))
    else:
        base = base.with_columns(pl.lit(1.0).alias("membership_weight"))
    rows = []
    for genre, group in base.group_by("track_genre", maintain_order=True):
        weights = group["membership_weight"].to_numpy().astype(float)
        row = {"track_genre": genre[0]}
        for feature in CONTINUOUS_AUDIO_FEATURES:
            values = group[feature].to_numpy().astype(float)
            for quantile in quantiles:
                suffix = f"q{int(quantile * 100):02d}"
                row[f"{feature}_{suffix}"] = _weighted_quantile(values, weights, quantile)
        rows.append(row)
    return pl.DataFrame(rows).sort("track_genre")


def robust_pca_profiles(profiles: pl.DataFrame, *, n_components: int = 2) -> tuple[pl.DataFrame, PCA]:
    """Robust-scale profile columns and return genre coordinates plus PCA."""

    value_columns = [column for column in profiles.columns if column != "track_genre"]
    values = profiles.select(value_columns).to_numpy()
    scaled = RobustScaler().fit_transform(values)
    pca = PCA(n_components=min(n_components, scaled.shape[1]), random_state=2026)
    coordinates = pca.fit_transform(scaled)
    return profiles.select("track_genre").with_columns(
        *[pl.Series(f"PC{i+1}", coordinates[:, i]) for i in range(coordinates.shape[1])]
    ), pca
