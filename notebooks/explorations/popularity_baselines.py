import marimo


__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import duckdb
    import marimo as mo
    import polars as pl
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    return (
        ColumnTransformer,
        LogisticRegression,
        OneHotEncoder,
        Path,
        Pipeline,
        SimpleImputer,
        StandardScaler,
        average_precision_score,
        duckdb,
        mo,
        pl,
        roc_auc_score,
        train_test_split,
    )


@app.cell
def _(Path, mo):
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"Input CSV not found: `{csv_path}`"))
    return (csv_path,)


@app.cell
def _(csv_path, duckdb):
    connection = duckdb.connect(":memory:")
    connection.execute(
        """
        CREATE TEMP TABLE tracks AS
        SELECT
            track_id,
            any_value(track_genre) AS display_genre,
            median(popularity) AS popularity,
            any_value(danceability) AS danceability,
            any_value(energy) AS energy,
            any_value(loudness) AS loudness,
            any_value(speechiness) AS speechiness,
            any_value(acousticness) AS acousticness,
            any_value(instrumentalness) AS instrumentalness,
            any_value(liveness) AS liveness,
            any_value(valence) AS valence,
            any_value(tempo) AS tempo,
            any_value(duration_ms) AS duration_ms,
            any_value(explicit) AS explicit
        FROM read_csv_auto(?, sample_size=-1, nullstr='')
        WHERE track_id IS NOT NULL
        GROUP BY track_id
        """,
        [str(csv_path)],
    )
    model_frame = connection.execute("SELECT * FROM tracks").pl()
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
    SimpleImputer,
    StandardScaler,
    average_precision_score,
    model_frame,
    mo,
    pl,
    roc_auc_score,
    run_models,
    train_test_split,
):
    mo.stop(not run_models.value, mo.md("Choose **Run baseline comparison** to train the bounded exploratory models."))
    numeric_features = [
        "danceability", "energy", "loudness", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo", "duration_ms",
    ]
    target_cutoff = float(model_frame.get_column("popularity").quantile(0.75))
    experiment_data = model_frame.with_columns((pl.col("popularity") >= target_cutoff).alias("high_popularity"))
    train_data, test_data = train_test_split(experiment_data.to_pandas(), test_size=0.25, random_state=2026, stratify=experiment_data.get_column("high_popularity").to_list())
    numeric_pipeline = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    feature_sets = {
        "audio only": (numeric_features, numeric_pipeline),
        "audio plus display genre": (
            numeric_features + ["display_genre"],
            ColumnTransformer([
                ("audio", numeric_pipeline, numeric_features),
                ("genre", OneHotEncoder(handle_unknown="ignore"), ["display_genre"]),
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
            "train_rows": len(train_data),
            "test_rows": len(test_data),
        })
    baseline_results = pl.DataFrame(baseline_rows).with_columns(pl.col(["roc_auc", "average_precision", "target_cutoff"]).round(4))
    return baseline_results, target_cutoff


@app.cell
def _(baseline_results, mo, target_cutoff):
    mo.vstack([
        mo.md(f"## Baseline association models\n\nThe target is popularity at or above the 75th-percentile cutoff (**{target_cutoff:.1f}**). This is a reproducible comparison of observable catalogue patterns, not a time-aware prediction of future hits."),
        mo.ui.table(baseline_results),
        mo.md("Use this notebook to decide whether a genre-aware baseline adds measurable held-out value before considering more complex models. Do not move a result into the final notebook without reviewing leakage, stability, and interpretation."),
    ])
    return


if __name__ == "__main__":
    app.run()
