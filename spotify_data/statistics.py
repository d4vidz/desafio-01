"""Small, testable multiplicity and heterogeneity helpers."""

from __future__ import annotations

from hashlib import sha256

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


def random_effects_pool(estimates: pl.DataFrame) -> dict[str, float]:
    """DerSimonian–Laird random-effects pooling from estimate and SE columns."""

    required = {"estimate", "standard_error"}
    if not required.issubset(estimates.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(estimates.columns))}")
    clean = estimates.drop_nulls(list(required))
    y = clean["estimate"].to_numpy().astype(float)
    se = clean["standard_error"].to_numpy().astype(float)
    if len(y) == 0:
        return {"estimate": float("nan"), "standard_error": float("nan"), "q": float("nan"), "i2": float("nan"), "n": 0.0}
    weights = 1 / np.maximum(se, 1e-12) ** 2
    fixed = float(np.sum(weights * y) / np.sum(weights))
    q = float(np.sum(weights * (y - fixed) ** 2))
    df = max(len(y) - 1, 1)
    c = float(np.sum(weights) - np.sum(weights**2) / np.sum(weights))
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    random_weights = 1 / (se**2 + tau2)
    pooled = float(np.sum(random_weights * y) / np.sum(random_weights))
    pooled_se = float(np.sqrt(1 / np.sum(random_weights)))
    return {
        "estimate": pooled,
        "standard_error": pooled_se,
        "q": q,
        "i2": max(0.0, (q - df) / q) if q > 0 else 0.0,
        "tau2": tau2,
        "n": float(len(y)),
    }


def artist_partition(artists: list[str] | np.ndarray, *, salt: str = "spotify-v0.1") -> np.ndarray:
    """Assign artists reproducibly to discovery (0) or confirmation (1).

    Hashing the grouping unit, rather than rows, prevents tracks by one artist
    from leaking across the two hypothesis stages and is stable across runs.
    """

    return np.asarray(
        [int(sha256(f"{salt}:{artist}".encode("utf-8")).hexdigest(), 16) % 2 for artist in artists],
        dtype=np.int8,
    )


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
