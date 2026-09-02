"""Bounded stability helpers for exploratory PCA/clustering."""

from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture


def clustering_stability(
    matrix: np.ndarray,
    *,
    k_values: range = range(2, 9),
    repeats: int = 8,
    sample_size: int = 6_000,
    seed: int = 2026,
) -> pl.DataFrame:
    """Compare K-means and Gaussian mixtures with bootstrap ARI stability.

    ARI is computed between a base fit and refits on resampled rows.  The
    bootstrap is intentionally bounded because this is an exploratory gate,
    not a search over a large model family.
    """

    values = np.asarray(matrix, dtype=float)
    rng = np.random.default_rng(seed)
    if len(values) > sample_size:
        values = values[rng.choice(len(values), sample_size, replace=False)]
    rows: list[dict[str, float | int | str]] = []
    for k in k_values:
        for algorithm in ("kmeans", "gmm"):
            def fit(data: np.ndarray):
                if algorithm == "kmeans":
                    return KMeans(n_clusters=k, n_init=10, random_state=seed).fit(data)
                return GaussianMixture(n_components=k, covariance_type="diag", random_state=seed).fit(data)

            base = fit(values)
            base_labels = base.predict(values)
            aris = []
            for repeat in range(repeats):
                indices = rng.choice(len(values), len(values), replace=True)
                bootstrap = fit(values[indices])
                aris.append(adjusted_rand_score(base_labels[indices], bootstrap.predict(values[indices])))
            rows.append({
                "algoritmo": algorithm,
                "k": k,
                "silhouette": float(silhouette_score(values, base_labels, sample_size=min(5_000, len(values)), random_state=seed)),
                "ARI_mediana": float(np.median(aris)),
                "ARI_p10": float(np.quantile(aris, 0.10)),
                "ARI_p90": float(np.quantile(aris, 0.90)),
                "gate_ari": bool(np.median(aris) >= 0.70),
            })
    return pl.DataFrame(rows).with_columns(pl.all().exclude(["algoritmo", "k", "gate_ari"]).round(3))
