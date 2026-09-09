"""Small, testable multiplicity and heterogeneity helpers."""

from __future__ import annotations

from hashlib import sha256
from statistics import NormalDist
from typing import Any

import numpy as np
import polars as pl
import statsmodels.api as sm


def holm_adjust(p_values: list[float] | np.ndarray) -> np.ndarray:
    """Return two-sided Holm step-down adjusted p-values."""

    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(values) - rank) * values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def bh_fdr(p_values: list[float] | np.ndarray) -> np.ndarray:
    """Return Benjamini–Hochberg adjusted p-values."""

    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 1.0
    for rank in range(len(values) - 1, -1, -1):
        index = order[rank]
        running = min(running, values[index] * len(values) / (rank + 1))
        adjusted[index] = min(1.0, running)
    return adjusted


def random_effects_pool(estimates: pl.DataFrame, *, alpha: float = 0.05) -> dict[str, float]:
    """Pool estimates with DerSimonian–Laird and return CI plus heterogeneity."""

    required = {"estimate", "standard_error"}
    if not required.issubset(estimates.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(estimates.columns))}")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    clean = estimates.drop_nulls(list(required))
    y = clean["estimate"].to_numpy().astype(float)
    se = clean["standard_error"].to_numpy().astype(float)
    if len(y) == 0:
        return {
            "estimate": float("nan"),
            "standard_error": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "q": float("nan"),
            "q_df": float("nan"),
            "i2": float("nan"),
            "tau2": float("nan"),
            "n": 0.0,
        }
    weights = 1 / np.maximum(se, 1e-12) ** 2
    fixed = float(np.sum(weights * y) / np.sum(weights))
    q = float(np.sum(weights * (y - fixed) ** 2))
    df = max(len(y) - 1, 0)
    c = float(np.sum(weights) - np.sum(weights**2) / np.sum(weights))
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    random_weights = 1 / (se**2 + tau2)
    pooled = float(np.sum(random_weights * y) / np.sum(random_weights))
    pooled_se = float(np.sqrt(1 / np.sum(random_weights)))
    z = NormalDist().inv_cdf(1 - alpha / 2)
    return {
        "estimate": pooled,
        "standard_error": pooled_se,
        "ci_low": pooled - z * pooled_se,
        "ci_high": pooled + z * pooled_se,
        "q": q,
        "q_df": float(df),
        "i2": max(0.0, (q - df) / q) if q > 0 and df > 0 else 0.0,
        "tau2": tau2,
        "n": float(len(y)),
    }


def coefficient_confidence_intervals(
    result: sm.regression.linear_model.RegressionResultsWrapper,
    parameter_indices: list[int] | np.ndarray,
    *,
    alpha: float = 0.05,
) -> np.ndarray:
    """Return two-sided confidence intervals for selected OLS parameters."""

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    intervals = np.asarray(result.conf_int(alpha=alpha), dtype=float)
    indices = np.asarray(parameter_indices, dtype=int)
    if np.any(indices < 0) or np.any(indices >= intervals.shape[0]):
        raise IndexError("parameter index is outside the fitted model")
    return intervals[indices]


def eligible_group_summary(
    frame: pl.DataFrame,
    *,
    group: str,
    cluster: str,
    min_tracks: int = 300,
    min_clusters: int = 100,
) -> pl.DataFrame:
    """Count every eligible group before any display or sampling limit."""

    required = {group, cluster}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(frame.columns))}")
    if min_tracks < 1 or min_clusters < 1:
        raise ValueError("eligibility thresholds must be positive")
    return (
        frame.drop_nulls([group, cluster])
        .group_by(group)
        .agg(
            pl.len().alias("n_tracks"),
            pl.col(cluster).n_unique().alias("n_artists"),
        )
        .filter((pl.col("n_tracks") >= min_tracks) & (pl.col("n_artists") >= min_clusters))
        .sort(["n_tracks", group], descending=[True, False])
    )


def artist_partition(artists: list[str] | np.ndarray, *, salt: str = "spotify-v0.1") -> np.ndarray:
    """Assign artists reproducibly to discovery (0) or confirmation (1).

    Hashing the grouping unit, rather than rows, prevents tracks by one artist
    from leaking across the two hypothesis stages and is stable across runs.
    """

    return np.asarray(
        [int(sha256(f"{salt}:{artist}".encode("utf-8")).hexdigest(), 16) % 2 for artist in artists],
        dtype=np.int8,
    )


def synthetic_imputation_metrics(
    observed: np.ndarray,
    masked: np.ndarray,
    mask: np.ndarray,
    *,
    transformer: Any | None = None,
    train_rows: np.ndarray | None = None,
) -> dict[str, float]:
    """Evaluate synthetic imputation without changing the real data.

    Complete-case reports row retention only.  An estimator is fitted on the
    supplied training rows and its error is computed exclusively on cells
    marked by ``mask`` against the untouched ``observed`` values.  The helper
    deliberately does not evaluate ``popularity`` or claim predictive MAE.
    """

    observed = np.asarray(observed, dtype=float)
    masked = np.asarray(masked, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    if observed.shape != masked.shape or observed.shape != mask.shape:
        raise ValueError("observed, masked, and mask must have identical shapes")
    if observed.ndim != 2 or observed.shape[0] == 0 or observed.shape[1] == 0:
        raise ValueError("imputation benchmark expects a non-empty 2D matrix")
    if np.any(masked[mask] == masked[mask]):
        raise ValueError("masked cells must be NaN in the masked matrix")
    if np.any(~mask & ~np.isfinite(masked)):
        raise ValueError("unmasked cells must remain finite")
    complete_rows = ~mask.any(axis=1)
    base = {
        "rows_used": float(complete_rows.sum()),
        "retention_fraction": float(complete_rows.mean()),
        "n_masked_cells": 0.0,
        "masked_mae": float("nan"),
    }
    if transformer is None:
        return base
    if train_rows is None:
        raise ValueError("train_rows is required when transformer is supplied")
    train_rows = np.asarray(train_rows, dtype=bool)
    if train_rows.shape != (observed.shape[0],) or not train_rows.any():
        raise ValueError("train_rows must select at least one row")
    fitted = transformer.fit(masked[train_rows])
    reconstructed = np.asarray(fitted.transform(masked), dtype=float)
    masked_cells = mask
    if not masked_cells.any():
        raise ValueError("mask must contain at least one masked cell")
    errors = np.abs(reconstructed[masked_cells] - observed[masked_cells])
    base.update(
        rows_used=float(observed.shape[0]),
        retention_fraction=1.0,
        n_masked_cells=float(masked_cells.sum()),
        masked_mae=float(np.mean(errors)),
    )
    return base


def fit_clustered_ols(
    frame: pl.DataFrame,
    *,
    outcome: str,
    features: list[str],
    controls: list[str],
    group: str,
) -> tuple[sm.regression.linear_model.RegressionResultsWrapper, list[str]]:
    """Fit a deterministic OLS with small categorical controls and clustered SEs.

    Numeric feature columns are standardized within the supplied frame. The
    caller owns the population (for example, confirmation or one genre).
    ``controls`` may contain numeric columns and a low-cardinality integer
    categorical ``time_signature``.
    """

    required = [outcome, *features, *controls, group]
    clean = frame.drop_nulls(required)
    numeric = clean.select(features).to_numpy().astype(float)
    means = numeric.mean(axis=0)
    scales = np.where(numeric.std(axis=0) > 0, numeric.std(axis=0), 1.0)
    parts = [(numeric - means) / scales]
    names = list(features)
    for column in controls:
        values = clean[column].to_numpy()
        if column == "time_signature":
            levels = sorted(set(values.tolist()))
            parts.extend([(values == level).astype(float)[:, None] for level in levels[1:]])
            names.extend([f"{column}[{level}]" for level in levels[1:]])
        else:
            # A subgroup can have a constant control (for example, all tracks
            # may share one mode).  Keeping it alongside the intercept creates
            # a rank-deficient design and unstable coefficient estimates.
            if np.unique(values).size > 1:
                parts.append(values.astype(float)[:, None])
                names.append(column)
    design = sm.add_constant(np.column_stack(parts), has_constant="add")
    result = sm.OLS(clean[outcome].to_numpy().astype(float), design).fit(
        cov_type="cluster", cov_kwds={"groups": clean[group].to_numpy()}
    )
    return result, names


def joint_wald_test(result: sm.regression.linear_model.RegressionResultsWrapper, n_features: int) -> float:
    """Return the p-value for the joint null that the first feature block is zero."""

    restriction = np.zeros((n_features, len(result.params)))
    restriction[:, 1 : n_features + 1] = np.eye(n_features)
    test = result.wald_test(restriction, scalar=False)
    return float(np.asarray(test.pvalue).reshape(-1)[0])
