"""Associações com popularity: confirmação pequena e screening controlado."""

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from hashlib import sha256
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import marimo as mo
    import numpy as np
    import polars as pl
    import plotly.graph_objects as go
    import statsmodels.api as sm
    from spotify_data import add_semantic_features, bh_fdr, build_data_layer, holm_adjust

    return Path, add_semantic_features, bh_fdr, build_data_layer, go, holm_adjust, mo, np, pl, sha256, sm


@app.cell
def _(Path, build_data_layer, mo):
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    single = db.execute("""
        SELECT t.*, MIN(ta.artist) AS primary_artist
        FROM tracks t JOIN track_artists ta USING(track_id)
        GROUP BY ALL HAVING COUNT(DISTINCT ta.artist) = 1
    """).pl()
    return db, layer, single, tracks


@app.cell
def _(go, mo, tracks):
    fig = go.Figure(go.Histogram(x=tracks["popularity"].to_numpy(), nbinsx=40))
    fig.update_layout(title="Distribuição da popularity canônica", xaxis_title="popularity", yaxis_title="faixas", height=380, template="plotly_white")
    zeros = int((tracks["popularity"] == 0).sum())
    mo.vstack([
        mo.md("# Popularity: associações observadas"),
        fig,
        mo.md(f"A métrica é contínua e observada no snapshot: mediana `{tracks['popularity'].median():.1f}`, zeros `{zeros:,}` e conflitos `{tracks.filter(tracks['popularity_conflict']).height:,}`. Isto não é forecasting temporal nem claim causal."),
    ])
    return (fig,)


@app.cell
def _(add_semantic_features, holm_adjust, mo, np, pl, sha256, single, sm):
    human = ["danceability", "energy", "valence", "acousticness", "instrumentalness", "speechiness"]
    controls = ["explicit", "key_sin", "key_cos", "mode", "time_signature", "log_duration_ms"]
    frame = add_semantic_features(single).drop_nulls([*human, *controls, "popularity", "primary_artist"])
    artists = frame["primary_artist"].to_list()
    split = np.array([int(sha256(str(artist).encode()).hexdigest(), 16) % 2 for artist in artists])
    confirmation = frame.filter(pl.Series("confirmation", split == 1))
    x_numeric = confirmation.select(human).to_numpy().astype(float)
    x_numeric = (x_numeric - x_numeric.mean(axis=0)) / np.where(x_numeric.std(axis=0) == 0, 1, x_numeric.std(axis=0))
    x_parts = [x_numeric, confirmation.select(["explicit", "key_sin", "key_cos", "mode", "log_duration_ms"]).to_numpy().astype(float)]
    time_values = confirmation["time_signature"].to_numpy()
    time_levels = sorted(set(time_values.tolist()))
    x_parts.append(np.column_stack([(time_values == level).astype(float) for level in time_levels[1:]]))
    x = sm.add_constant(np.column_stack(x_parts), has_constant="add")
    model = sm.OLS(confirmation["popularity"].to_numpy(), x).fit(cov_type="cluster", cov_kwds={"groups": confirmation["primary_artist"].to_numpy()})
    rows = []
    for index, _human_feature in enumerate(human, start=1):
        rows.append({"feature": _human_feature, "effect_per_sd": float(model.params[index]), "se_cluster": float(model.bse[index]), "p_value": float(model.pvalues[index])})
    association = pl.DataFrame(rows).with_columns(
        pl.Series("p_holm", holm_adjust([row["p_value"] for row in rows])),
    )
    association = association.with_columns((pl.col("effect_per_sd").abs() >= 1).alias("relevancia_pratica_1_pt"))
    omnibus = {"n_tracks": confirmation.height, "n_artists": confirmation["primary_artist"].n_unique(), "r_squared": float(model.rsquared), "family": "seis features, teste conjunto + Holm"}
    mo.vstack([mo.md("## 1. Família confirmatória: painel humano"), mo.ui.table(association.with_columns(pl.col(["effect_per_sd", "se_cluster", "p_value", "p_holm"]).round(4))), mo.ui.table(pl.DataFrame([omnibus]))])
    return association, confirmation, frame, human, model, time_levels


@app.cell
def _(association, bh_fdr, mo, np, pl, frame, human, sm):
    screen_rows = []
    for feature in human + ["loudness", "liveness", "tempo", "duration_ms"]:
        subset = frame.drop_nulls([feature])
        _screen_x = sm.add_constant(subset.select([feature]).to_numpy().astype(float), has_constant="add")
        fit = sm.OLS(subset["popularity"].to_numpy(), _screen_x).fit()
        screen_rows.append({"feature": feature, "p_value": float(fit.pvalues[1]), "effect": float(fit.params[1]), "n": subset.height})
    screening = pl.DataFrame(screen_rows).with_columns(pl.Series("p_bh", bh_fdr([row["p_value"] for row in screen_rows])))
    mo.vstack([
        mo.md("## 2. Screening exploratório"),
        mo.ui.table(screening.with_columns(pl.col(["p_value", "effect", "p_bh"]).round(4))),
        mo.md("O screening é gerador de hipótese e controla BH-FDR 0,05. A tabela não substitui a família confirmatória ajustada, a covariância agrupada nem a análise por gênero."),
    ])
    return (screening,)


@app.cell
def _(association, mo, tracks):
    conflict_free = tracks.filter(~tracks["popularity_conflict"])
    mo.vstack([
        mo.md("## 3. Sensibilidades e teto de claims"),
        mo.ui.table(association),
        mo.md(f"Sensibilidade preparada: repetir os resultados na população sem os `{tracks.height - conflict_free.height}` conflitos. Outliers, zeros e duração longa devem ser preservados e testados com transformações robustas/log; não há remoção automática por IQR. Claims permitidos são associação ajustada e, em notebook próprio, previsão held-out; não causalidade, comportamento de ouvintes ou sucesso futuro."),
    ])
    return


if __name__ == "__main__":
    app.run()
