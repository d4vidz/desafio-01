"""Small, testable multiplicity and heterogeneity helpers."""

from __future__ import annotations

import numpy as np
import polars as pl


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
