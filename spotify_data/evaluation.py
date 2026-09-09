"""Deterministic, group-aware evaluation of observed popularity.

The public baseline API keeps the evaluation protocol separate from the
legacy tabular helpers. ``run_evaluation`` retains session predictions for
paired uncertainty estimates, while ``EvaluationResult.artifact`` emits only
bounded summaries and examples suitable for version control.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

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
    """A named split in the baseline protocol."""

    name: str
    grouped: bool


@dataclass(frozen=True)
class EvaluationSpec:
    """Configuration for the reproducible popularity baseline.

    ``feature_columns`` is deliberately explicit. ``track_id`` is required
    as an input identity column but is never passed to a model. The default
    protocol uses five repetitions; small tests and bounded smoke runs can
    request fewer repetitions explicitly.
    """

    feature_columns: tuple[str, ...]
    group_column: str = "primary_artist"
    target_column: str = "popularity"
    repeats: int = 5
    test_size: float = 0.2
    seed: int = 2026
    bootstrap_replicates: int = 400
    bootstrap_seed: int = 2027
    promotion_mae_gain: float = 0.5
    protocol_version: str = "0.2"

    def __post_init__(self) -> None:
        features = tuple(self.feature_columns)
        object.__setattr__(self, "feature_columns", features)
        if not features:
            raise ValueError("At least one evaluation feature is required")
        if len(set(features)) != len(features):
            raise ValueError("Evaluation features must be unique")
        forbidden = {"track_id", self.target_column, self.group_column}
        leaked = sorted(forbidden.intersection(features))
        if leaked:
            raise ValueError(f"Evaluation features cannot include: {', '.join(leaked)}")
        if self.repeats < 1:
            raise ValueError("repeats must be at least 1")
        if not 0 < self.test_size < 1:
            raise ValueError("test_size must be between 0 and 1")
        if self.bootstrap_replicates < 1:
            raise ValueError("bootstrap_replicates must be at least 1")
        if self.promotion_mae_gain < 0:
            raise ValueError("promotion_mae_gain cannot be negative")


@dataclass(frozen=True)
class ModelSummary:
    """Typed headline metric used by notebook narratives."""

    split: str
    model: str
    mae_mean: float


@dataclass(frozen=True)
class EvaluationResult:
    """Auditable session result; notebook renderers must display bounded views."""

    spec: EvaluationSpec
    metrics: pl.DataFrame
    predictions: pl.DataFrame
    partitions: pl.DataFrame
    paired_intervals: pl.DataFrame
    provenance: dict[str, Any]

    @property
    def summary(self) -> pl.DataFrame:
        """Return aggregate metrics for this run."""

        return summarize_evaluation(self.metrics)

    def artifact(self) -> dict[str, Any]:
        """Return a bounded JSON-safe handoff without full predictions."""

        error_bins = (
            self.predictions.with_columns(
                pl.col("absolute_error")
                .cut([5.0, 10.0, 20.0], labels=["0–5", "5–10", "10–20", "20+"])
                .alias("error_bin")
            )
            .group_by(["split", "modelo", "error_bin"])
            .len()
            .sort(["split", "modelo", "error_bin"])
        )
        examples = (
            self.predictions.sort(
                ["absolute_error", "track_id"],
                descending=[True, False],
            )
            .group_by(["split", "modelo"], maintain_order=True)
            .head(5)
        )
        return {
            "version": 1,
            "spec": asdict(self.spec),
            "provenance": self.provenance,
            "metrics": self.summary.to_dicts(),
            "paired_intervals": self.paired_intervals.to_dicts(),
            "partitions": self.partitions.to_dicts(),
            "error_bins": error_bins.to_dicts(),
            "bounded_examples": examples.to_dicts(),
            "full_predictions": "session-only; not committed",
        }

    def write_json(self, path: str | Path) -> None:
        """Write the bounded handoff artifact with canonical formatting."""

        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.artifact(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )


SPLITS = (
    SplitSpec("artista não visto", grouped=True),
    SplitSpec("aleatório diagnóstico", grouped=False),
)


def make_models(*, seed: int = 2026) -> dict[str, object | None]:
    """Create fresh baseline estimators for one fold.

    The Ridge scaler is inside the pipeline so it is fitted on the training
    fold only. A fresh dictionary is created for every fold by
    ``_fit_predict``.
    """

    return {
        "dummy mediana": None,
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=140,
            max_leaf_nodes=31,
            learning_rate=0.05,
            l2_regularization=1.0,
            random_state=seed,
        ),
    }


def _single_artist_mask(frame: pl.DataFrame, group_column: str) -> pl.Expr:
    """Return the strict single-artist population when metadata is present."""

    if "artist_count" in frame.columns:
        return (pl.col("artist_count") == 1) & pl.col(group_column).is_not_null()
    if "artists" in frame.columns:
        return (
            pl.col("artists").fill_null("").str.count_matches(";") == 0
        ) & pl.col(group_column).is_not_null()
    return pl.col(group_column).is_not_null()


def _fit_predict(
    x: np.ndarray,
    y: np.ndarray,
    train_index: np.ndarray,
    test_index: np.ndarray,
    *,
    seed: int,
) -> dict[str, np.ndarray]:
    """Fit every model on one training fold and predict its test fold."""

    predictions: dict[str, np.ndarray] = {
        "dummy mediana": np.full(len(test_index), np.median(y[train_index]))
    }
    for name, model in make_models(seed=seed).items():
        if model is None:
            continue
        # The fit call is intentionally inside the fold loop. This keeps
        # StandardScaler statistics and estimator state fold-local.
        model.fit(x[train_index], y[train_index])
        predictions[name] = model.predict(x[test_index])
    return predictions


def _stable_hash(values: np.ndarray) -> str:
    """Hash a set-like sequence independently of input order."""

    payload = "\n".join(sorted(str(value) for value in values)).encode("utf-8")
    return sha256(payload).hexdigest()


def _paired_artist_intervals(
    predictions: pl.DataFrame,
    spec: EvaluationSpec,
    *,
    baseline: str = "dummy mediana",
) -> pl.DataFrame:
    """Bootstrap paired MAE deltas after aggregating rows within artist."""

    rows: list[dict[str, float | int | str | bool]] = []
    for split in predictions["split"].unique().sort().to_list():
        split_frame = predictions.filter(pl.col("split") == split)
        baseline_errors = split_frame.filter(pl.col("modelo") == baseline).select(
            ["repeticao", "track_id", "primary_artist", "absolute_error"]
        ).rename({"absolute_error": "baseline_error"})
        for model in (
            split_frame.filter(pl.col("modelo") != baseline)["modelo"]
            .unique()
            .sort()
            .to_list()
        ):
            paired = (
                split_frame.filter(pl.col("modelo") == model)
                .join(
                    baseline_errors,
                    on=["repeticao", "track_id", "primary_artist"],
                    how="inner",
                    validate="1:1",
                )
                .with_columns(
                    (pl.col("absolute_error") - pl.col("baseline_error")).alias(
                        "delta_mae"
                    )
                )
                .group_by("primary_artist")
                .agg(pl.col("delta_mae").mean())
                .sort("primary_artist")
            )
            artist_deltas = paired["delta_mae"].to_numpy()
            rng = np.random.default_rng(
                spec.bootstrap_seed
                + sum(ord(character) for character in f"{split}:{model}")
            )
            draw_indices = rng.integers(
                0,
                len(artist_deltas),
                size=(spec.bootstrap_replicates, len(artist_deltas)),
            )
            bootstrap_means = artist_deltas[draw_indices].mean(axis=1)
            mean_delta = float(artist_deltas.mean())
            ci_low, ci_high = np.quantile(bootstrap_means, [0.025, 0.975])
            rows.append(
                {
                    "split": split,
                    "modelo": model,
                    "baseline": baseline,
                    "artists": len(artist_deltas),
                    "delta_mae": mean_delta,
                    "ci95_low": float(ci_low),
                    "ci95_high": float(ci_high),
                    "promotion_gate": bool(
                        mean_delta <= -spec.promotion_mae_gain and ci_high < 0
                    ),
                }
            )
    return pl.DataFrame(rows)


def run_evaluation(frame: pl.DataFrame, spec: EvaluationSpec) -> EvaluationResult:
    """Evaluate the three baselines on grouped and diagnostic random splits.

    The primary split is ``artista não visto`` and uses
    :class:`GroupShuffleSplit`, so no value of ``spec.group_column`` can occur
    in both train and test. The random split is a deliberately optimistic
    diagnostic. Rows with missing required values are removed before either
    split, and the same filtered population is used for all models.
    """

    if not isinstance(spec, EvaluationSpec):
        raise TypeError("spec must be an EvaluationSpec")

    required = [
        "track_id",
        spec.target_column,
        spec.group_column,
        *spec.feature_columns,
    ]
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"Missing evaluation columns: {', '.join(missing)}")

    # ``track_id`` is retained only for input validation and canonical grain;
    # the model matrix is constructed from feature_columns below.
    data = (
        frame.filter(_single_artist_mask(frame, spec.group_column))
        .select(required)
        .drop_nulls()
    )
    if data.is_empty():
        raise ValueError("The strict unseen-single-artist population is empty")
    if data["track_id"].n_unique() != data.height:
        raise ValueError("Evaluation requires exactly one row per track_id")

    x = data.select(spec.feature_columns).to_numpy()
    y = data[spec.target_column].to_numpy()
    groups = data[spec.group_column].to_numpy()
    rows: list[dict[str, float | int | str]] = []
    prediction_rows: list[dict[str, float | int | str]] = []
    partition_rows: list[dict[str, float | int | str]] = []

    for split in SPLITS:
        if split.grouped:
            splitter = GroupShuffleSplit(
                n_splits=spec.repeats,
                test_size=spec.test_size,
                random_state=spec.seed,
            )
            iterator = splitter.split(x, y, groups=groups)
        else:
            splitter = ShuffleSplit(
                n_splits=spec.repeats,
                test_size=spec.test_size,
                random_state=spec.seed,
            )
            iterator = splitter.split(x, y)

        for repetition, (train_index, test_index) in enumerate(iterator, start=1):
            predictions = _fit_predict(
                x, y, train_index, test_index, seed=spec.seed + repetition
            )
            train_artists = np.unique(groups[train_index])
            test_artists = np.unique(groups[test_index])
            partition_rows.append(
                {
                    "split": split.name,
                    "repeticao": repetition,
                    "train_rows": int(len(train_index)),
                    "test_rows": int(len(test_index)),
                    "train_artists": int(len(train_artists)),
                    "test_artists": int(len(test_artists)),
                    "artist_overlap": int(
                        len(set(train_artists).intersection(test_artists))
                    ),
                    "train_track_sha256": _stable_hash(
                        data["track_id"].to_numpy()[train_index]
                    ),
                    "test_track_sha256": _stable_hash(
                        data["track_id"].to_numpy()[test_index]
                    ),
                }
            )
            for model_name, predicted in predictions.items():
                rows.append(
                    {
                        "split": split.name,
                        "repeticao": repetition,
                        "modelo": model_name,
                        "MAE": float(mean_absolute_error(y[test_index], predicted)),
                        "RMSE": float(
                            mean_squared_error(y[test_index], predicted) ** 0.5
                        ),
                        "R2": float(r2_score(y[test_index], predicted)),
                        "train_rows": int(len(train_index)),
                        "test_rows": int(len(test_index)),
                        "train_artists": int(np.unique(groups[train_index]).size),
                        "test_artists": int(np.unique(groups[test_index]).size),
                    }
                )
                for row_index, prediction in zip(test_index, predicted, strict=True):
                    row_position = int(row_index)
                    observed = float(y[row_position])
                    prediction_rows.append(
                        {
                            "split": split.name,
                            "repeticao": repetition,
                            "modelo": model_name,
                            "track_id": str(data["track_id"][row_position]),
                            "primary_artist": str(groups[row_position]),
                            "observed": observed,
                            "predicted": float(prediction),
                            "absolute_error": abs(observed - float(prediction)),
                        }
                    )

    metric_frame = pl.DataFrame(rows)
    prediction_frame = pl.DataFrame(prediction_rows)
    partition_frame = pl.DataFrame(partition_rows)
    spec_payload = json.dumps(asdict(spec), sort_keys=True).encode("utf-8")
    provenance = {
        "protocol_version": spec.protocol_version,
        "spec_sha256": sha256(spec_payload).hexdigest(),
        "population_sha256": _stable_hash(data["track_id"].to_numpy()),
        "population_rows": data.height,
        "prediction_rows": prediction_frame.height,
    }
    return EvaluationResult(
        spec=spec,
        metrics=metric_frame,
        predictions=prediction_frame,
        partitions=partition_frame,
        paired_intervals=_paired_artist_intervals(prediction_frame, spec),
        provenance=provenance,
    )


def summarize_evaluation(
    evaluation: EvaluationResult | pl.DataFrame,
) -> pl.DataFrame:
    """Aggregate fold metrics by split and model.

    Accepting both ``EvaluationResult`` and its metrics table makes the new
    API convenient while keeping the old ``summarize_metrics`` call shape
    source-compatible.
    """

    results = (
        evaluation.metrics if isinstance(evaluation, EvaluationResult) else evaluation
    )
    required = {"split", "modelo", "MAE", "RMSE", "R2"}
    missing = sorted(required.difference(results.columns))
    if missing:
        raise ValueError(f"Missing evaluation metric columns: {', '.join(missing)}")
    return (
        results.group_by(["split", "modelo"])
        .agg(
            pl.col("MAE").mean().alias("MAE_medio"),
            pl.col("MAE").std().alias("MAE_sd"),
            pl.col("RMSE").mean().alias("RMSE_medio"),
            pl.col("R2").mean().alias("R2_medio"),
        )
        .sort(["split", "MAE_medio", "modelo"])
        .with_columns(pl.all().exclude(["split", "modelo"]).round(3))
    )


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
    """Legacy wrapper returning the original per-fold metrics table."""

    spec = EvaluationSpec(
        tuple(feature_columns),
        group_column=group_column,
        target_column=target_column,
        repeats=repeats,
        test_size=test_size,
        seed=seed,
    )
    return run_evaluation(frame, spec).metrics


def summarize_metrics(results: pl.DataFrame) -> pl.DataFrame:
    """Backward-compatible alias for :func:`summarize_evaluation`."""

    return summarize_evaluation(results)


def best_model_summary(summary: pl.DataFrame, split: str) -> ModelSummary:
    """Return the lowest-MAE model, using the model name as tie-breaker."""

    candidates = summary.filter(pl.col("split") == split).sort(
        ["MAE_medio", "modelo"]
    )
    if candidates.is_empty():
        raise ValueError(f"No model summary rows for split: {split}")
    row = candidates.row(0, named=True)
    return ModelSummary(
        split=str(row["split"]),
        model=str(row["modelo"]),
        mae_mean=float(row["MAE_medio"]),
    )
