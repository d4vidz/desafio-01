import marimo


__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path
    _repo_root = Path(__file__).resolve().parents[2]
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

    import marimo as mo
    import polars as pl
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    return (
        ColumnTransformer,
        LogisticRegression,
        OneHotEncoder,
        Path,
        Pipeline,
        StandardScaler,
        GroupShuffleSplit,
        average_precision_score,
        mo,
        pl,
        roc_auc_score,
    )


@app.cell
def _(Path, mo):
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"Input CSV not found: `{csv_path}`"))
    return (csv_path,)


@app.cell
def _(csv_path):
    from spotify_data import build_duckdb_layer
    connection = build_duckdb_layer(csv_path)
    model_frame = connection.execute("""
      SELECT t.*, min_by(a.artist, a.artist_position) AS primary_artist
      FROM tracks t JOIN track_artists a USING (track_id) GROUP BY ALL
    """).pl()
    return (model_frame,)


@app.cell
def _(mo):
    run_models = mo.ui.run_button(label="Run baseline comparison", kind="success")
    run_models
    return (run_models,)


@app.cell
def _(
    ColumnTransformer,
    LogisticRegression,
    OneHotEncoder,
    Pipeline,
    StandardScaler,
    GroupShuffleSplit,
    average_precision_score,
    model_frame,
    mo,
    pl,
    roc_auc_score,
    run_models,
):
    mo.stop(not run_models.value, mo.md("Choose **Run baseline comparison** to train the bounded exploratory models."))
    numeric_features = [
        "danceability", "energy", "loudness", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo", "duration_ms",
    ]
    target_cutoff = float(model_frame.get_column("popularity").quantile(0.75))
    experiment_data = model_frame.with_columns((pl.col("popularity") >= target_cutoff).alias("high_popularity"))
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=2026)
    train_idx, test_idx = next(splitter.split(experiment_data, groups=experiment_data["primary_artist"].to_numpy()))
    train_data, test_data = experiment_data[train_idx], experiment_data[test_idx]
    numeric_pipeline = Pipeline([("scale", StandardScaler())])
    feature_sets = {
        "audio only": (numeric_features, numeric_pipeline),
        "audio plus representative genre": (
            numeric_features + ["representative_track_genre"],
            ColumnTransformer([
                ("audio", numeric_pipeline, numeric_features),
                ("genre", OneHotEncoder(handle_unknown="ignore"), ["representative_track_genre"]),
            ]),
        ),
    }
    baseline_rows = []
    for model_name, (columns, transformer) in feature_sets.items():
        pipeline = Pipeline([("features", transformer), ("model", LogisticRegression(max_iter=600, class_weight="balanced"))])
        pipeline.fit(train_data[columns], train_data["high_popularity"])
        probabilities = pipeline.predict_proba(test_data[columns])[:, 1]
        baseline_rows.append({
            "model": model_name,
            "roc_auc": roc_auc_score(test_data["high_popularity"], probabilities),
            "average_precision": average_precision_score(test_data["high_popularity"], probabilities),
            "target_cutoff": target_cutoff,
            "train_rows": train_data.height,
            "test_rows": test_data.height,
        })
    baseline_results = pl.DataFrame(baseline_rows).with_columns(pl.col(["roc_auc", "average_precision", "target_cutoff"]).round(4))
    return baseline_results, target_cutoff


@app.cell
def _(baseline_results, mo, target_cutoff):
    mo.vstack([
        mo.md(f"## Secondary threshold-sensitivity lens\n\nThe target is popularity at or above the global 75th-percentile cutoff (**{target_cutoff:.1f}**). Artists are kept together across train/test. This secondary classification lens does not replace the continuous grouped regression in the final notebook and is not a time-aware prediction of future hits."),
        mo.ui.table(baseline_results),
        mo.md("Use this notebook to decide whether a genre-aware baseline adds measurable held-out value before considering more complex models. Do not move a result into the final notebook without reviewing leakage, stability, and interpretation."),
    ])
    return


if __name__ == "__main__":
    app.run()
