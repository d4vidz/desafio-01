"""Validation of observed popularity with unseen-artist splits."""

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import marimo as mo
    import polars as pl
    from spotify_data import add_semantic_features, build_data_layer
    from spotify_data.evaluation import evaluate_regression, summarize_metrics
    return Path, add_semantic_features, build_data_layer, evaluate_regression, mo, pl, summarize_metrics


@app.cell
def _(Path, build_data_layer, mo):
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    # Primary evaluation population: one artist per track. Collaborations are
    # reported separately in the final protocol instead of leaking across folds.
    model_frame = db.execute("""
        SELECT t.*, MIN(ta.artist) AS primary_artist
        FROM tracks t JOIN track_artists ta USING(track_id)
        GROUP BY ALL HAVING COUNT(DISTINCT ta.artist) = 1
        ORDER BY track_id
    """).pl()
    return layer, model_frame


@app.cell
def _(add_semantic_features, evaluate_regression, model_frame, mo, pl, summarize_metrics):
    numeric = ["danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo", "log_duration_ms", "key_sin", "key_cos", "explicit_binary", "mode_binary"]
    prepared = add_semantic_features(model_frame)
    # A deterministic cap keeps the exploratory notebook responsive. The
    # final run can remove the cap without changing the split/model protocol.
    prepared = prepared.sample(n=min(40_000, prepared.height), seed=2026)
    results = evaluate_regression(prepared, numeric, repeats=5)
    summary = summarize_metrics(results)
    grouped = summary.filter(pl.col("split") == "artista não visto")
    mo.vstack([
        mo.md("# Validação preditiva: popularity observada"),
        mo.ui.table(summary),
        mo.md("MAE é a métrica primária; RMSE e R² são secundárias. O split por artista não visto é principal; o aleatório é apenas diagnóstico otimista. Um ganho só será promovido se reduzir pelo menos 0,5 ponto de MAE e o intervalo pareado por bootstrap agrupado excluir zero."),
    ])
    return grouped, prepared, results, summary


@app.cell
def _(mo, pl, prepared):
    collaboration = pl.DataFrame({
        "populacao": ["faixas canônicas", "faixas de artista único", "faixas colaborativas"],
        "linhas": [prepared.height, prepared.filter(pl.col("primary_artist").is_not_null()).height, 0],
        "uso": ["contexto", "split primário", "estratos all/some/none seen no protocolo"],
    })
    mo.vstack([mo.md("## Escopo e limites"), mo.ui.table(collaboration), mo.md("IDs, nomes de faixa, artista e álbum nunca são preditores. Features de artista/grafo só podem entrar em ablations calculadas dentro do treino e com OOV explícito. Esta entrega estima generalização contemporânea no snapshot; não prevê o próximo hit." )])
    return (collaboration,)


if __name__ == "__main__":
    app.run()
