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
    null_repeats: int = 20,
    sample_size: int = 6_000,
    seed: int = 2026,
) -> pl.DataFrame:
    """Compare K-means and Gaussian mixtures with bootstrap ARI stability.

    ARI is computed between a base fit and refits on resampled rows. Separation
    is compared with a reference distribution made by independently permuting
    every feature, preserving univariate marginals while removing multivariate
    structure. Both computations are intentionally bounded.
    """

    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2 or len(values) < 3:
        raise ValueError("matrix must contain at least three rows")
    if repeats < 1 or null_repeats < 1:
        raise ValueError("repeats and null_repeats must be at least 1")
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
            observed_silhouette = float(
                silhouette_score(
                    values,
                    base_labels,
                    sample_size=min(5_000, len(values)),
                    random_state=seed,
                )
            )
            aris = []
            for repeat in range(repeats):
                indices = rng.choice(len(values), len(values), replace=True)
                bootstrap = fit(values[indices])
                aris.append(adjusted_rand_score(base_labels[indices], bootstrap.predict(values[indices])))
            null_silhouettes = []
            for _ in range(null_repeats):
                reference = np.column_stack(
                    [rng.permutation(values[:, column]) for column in range(values.shape[1])]
                )
                reference_fit = fit(reference)
                reference_labels = reference_fit.predict(reference)
                null_silhouettes.append(
                    silhouette_score(
                        reference,
                        reference_labels,
                        sample_size=min(5_000, len(reference)),
                        random_state=seed,
                    )
                )
            null_p95 = float(np.quantile(null_silhouettes, 0.95))
            median_ari = float(np.median(aris))
            rows.append({
                "algoritmo": algorithm,
                "k": k,
                "silhouette": observed_silhouette,
                "null_silhouette_p95": null_p95,
                "ARI_mediana": median_ari,
                "ARI_p10": float(np.quantile(aris, 0.10)),
                "ARI_p90": float(np.quantile(aris, 0.90)),
                "gate_ari": bool(median_ari >= 0.70),
                "gate_separacao": bool(observed_silhouette > null_p95),
                "gate_robusto": bool(median_ari >= 0.70 and observed_silhouette > null_p95),
            })
    return pl.DataFrame(rows).with_columns(
        pl.all().exclude(
            ["algoritmo", "k", "gate_ari", "gate_separacao", "gate_robusto"]
        ).round(3)
    )
