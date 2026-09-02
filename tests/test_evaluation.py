import polars as pl

from spotify_data.evaluation import evaluate_regression, summarize_metrics


def test_grouped_evaluation_never_uses_test_artists_in_training_and_is_bounded():
    rows = []
    for artist in ("a", "b", "c", "d", "e", "f"):
        for track_number in range(3):
            rows.append({
                "track_id": f"{artist}-{track_number}", "primary_artist": artist,
                "popularity": 10 + track_number, "energy": 0.2 + track_number / 10,
                "danceability": 0.3 + track_number / 10,
            })
    frame = pl.DataFrame(rows)
    results = evaluate_regression(frame, ["energy", "danceability"], repeats=2)
    assert set(results["split"].unique()) == {"artista não visto", "aleatório diagnóstico"}
    grouped = results.filter(pl.col("split") == "artista não visto")
    assert (grouped["train_artists"] + grouped["test_artists"] <= 6).all()
    assert summarize_metrics(results).height == 6
