"""Bounded, group-aware continuous popularity evaluation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit, ShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class SplitSpec:
    name: str
    grouped: bool


@dataclass(frozen=True)
class ModelSummary:
    """Typed headline metric used by notebook narratives."""

    split: str
    model: str
    mae_mean: float


SPLITS = (SplitSpec("artista não visto", True), SplitSpec("aleatório diagnóstico", False))


def make_models() -> dict[str, object]:
    return {
        "dummy mediana": None,
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=140, max_leaf_nodes=31, learning_rate=0.05,
            l2_regularization=1.0, random_state=2026,
        ),
    }


def evaluate_regression(
    frame: pl.DataFrame,
    feature_columns: list[str],
    *,
    group_column: str = "primary_artist",
    target_column: str = "popularity",
    repeats: int = 5,
    test_size: float = 0.2,
    seed: int = 2026,
) -> pl.DataFrame:
    """Compare the mandated baselines with fold-local model fitting."""

    data = frame.select(["track_id", target_column, group_column, *feature_columns]).drop_nulls()
    x = data.select(feature_columns).to_numpy()
    y = data[target_column].to_numpy()
    groups = data[group_column].to_numpy()
    rows: list[dict[str, float | int | str]] = []
    for split in SPLITS:
        splitter = (GroupShuffleSplit(n_splits=repeats, test_size=test_size, random_state=seed)
                    if split.grouped else ShuffleSplit(n_splits=repeats, test_size=test_size, random_state=seed))
        iterator = splitter.split(x, y, groups=groups) if split.grouped else splitter.split(x, y)
        for repeat, (train_idx, test_idx) in enumerate(iterator, start=1):
            models = make_models()
            predictions = {"dummy mediana": np.full(len(test_idx), np.median(y[train_idx]))}
            for name, model in list(models.items())[1:]:
                model.fit(x[train_idx], y[train_idx])
                predictions[name] = model.predict(x[test_idx])
            for name, predicted in predictions.items():
                rows.append({
                    "split": split.name,
                    "repeticao": repeat,
                    "modelo": name,
                    "MAE": float(mean_absolute_error(y[test_idx], predicted)),
                    "RMSE": float(mean_squared_error(y[test_idx], predicted) ** 0.5),
                    "R2": float(r2_score(y[test_idx], predicted)),
                    "train_rows": int(len(train_idx)),
                    "test_rows": int(len(test_idx)),
                    "train_artists": int(np.unique(groups[train_idx]).size),
                    "test_artists": int(np.unique(groups[test_idx]).size),
                })
    return pl.DataFrame(rows)


def summarize_metrics(results: pl.DataFrame) -> pl.DataFrame:
    return (
        results.group_by(["split", "modelo"])
        .agg(
            pl.col("MAE").mean().alias("MAE_medio"),
            pl.col("MAE").std().alias("MAE_sd"),
            pl.col("RMSE").mean().alias("RMSE_medio"),
            pl.col("R2").mean().alias("R2_medio"),
        )
        .sort(["split", "MAE_medio"])
        .with_columns(pl.all().exclude(["split", "modelo"]).round(3))
    )


def best_model_summary(summary: pl.DataFrame, split: str) -> ModelSummary:
    """Return the lowest-MAE model without exposing notebook code to schema strings."""

    candidates = summary.filter(pl.col("split") == split).sort("MAE_medio")
    if candidates.is_empty():
        raise ValueError(f"No model summary rows for split: {split}")
    row = candidates.row(0, named=True)
    return ModelSummary(
        split=str(row["split"]),
        model=str(row["modelo"]),
        mae_mean=float(row["MAE_medio"]),
    )
