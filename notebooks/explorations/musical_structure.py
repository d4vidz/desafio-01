"""PCA, loadings and stability-gated clustering of the audio space."""

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
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import RobustScaler, StandardScaler
    from spotify_data import CONTINUOUS_AUDIO_FEATURES, build_data_layer, clustering_stability
    return CONTINUOUS_AUDIO_FEATURES, PCA, Path, RobustScaler, StandardScaler, build_data_layer, clustering_stability, go, mo, np, pl


@app.cell
def _(Path, build_data_layer, mo):
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    return layer, tracks


@app.cell
def _(CONTINUOUS_AUDIO_FEATURES, PCA, RobustScaler, StandardScaler, mo, np, pl, tracks):
    features = list(CONTINUOUS_AUDIO_FEATURES)
    frame = tracks.select(["track_id", "representative_track_genre", *features]).drop_nulls()
    frame = frame.sample(n=min(6_000, frame.height), seed=2026)
    standard = StandardScaler().fit_transform(frame.select(features).to_numpy())
    robust_scaled = RobustScaler().fit_transform(frame.select(features).to_numpy())
    pca = PCA(n_components=3, random_state=2026).fit(standard)
    coordinates = pca.transform(standard)
    loadings = pl.DataFrame({"feature": features, "PC1": pca.components_[0], "PC2": pca.components_[1], "PC3": pca.components_[2]}).with_columns(pl.all().exclude("feature").round(3))
    pca_frame = frame.select(["track_id", "representative_track_genre"]).with_columns(*[pl.Series(f"PC{i+1}", coordinates[:, i]) for i in range(3)])
    variance = pl.DataFrame({"componente": ["PC1", "PC2", "PC3"], "variancia_explicada": pca.explained_variance_ratio_}).with_columns(pl.col("variancia_explicada").round(4))
    return features, loadings, pca_frame, robust_scaled, standard, variance


@app.cell
def _(go, loadings, mo, pca_frame, variance):
    plot = pca_frame.sample(n=min(4_000, pca_frame.height), seed=2026)
    fig = go.Figure(go.Scattergl(x=plot["PC1"].to_numpy(), y=plot["PC2"].to_numpy(), mode="markers", marker={"size": 5, "opacity": 0.45, "color": plot["PC3"].to_numpy(), "colorscale": "Viridis", "colorbar": {"title": "PC3"}}, text=plot["representative_track_genre"].to_list(), hovertemplate="gênero=%{text}<br>PC1=%{x:.2f}<br>PC2=%{y:.2f}<extra></extra>"))
    fig.update_layout(title="PCA 2D — cor por PC3; amostra bounded", height=520, template="plotly_white")
    mo.vstack([mo.md("# Musical structure: PCA e clustering"), fig, mo.hstack([mo.ui.table(variance), mo.ui.table(loadings)], widths="equal"), mo.md("PCA usa as dez features contínuas, padronização e `duration_ms` bruto nesta primeira versão. A RobustScaler fica como sensibilidade; loadings e variância são obrigatórios para interpretar os eixos." )])
    return (fig,)


@app.cell
def _(clustering_stability, mo, standard):
    stability = clustering_stability(standard, k_values=range(2, 9), repeats=2, sample_size=3_000)
    robust_candidates = stability.filter(stability["gate_ari"])
    claim = "há candidatos estáveis para inspeção" if robust_candidates.height else "não há clusters naturais robustos pelo gate ARI ≥ 0,70"
    mo.vstack([mo.md("## Estabilidade e gate de clusters"), mo.ui.table(stability), mo.md(f"Conclusão provisória: **{claim}**. O gate completo ainda deve contrastar separação com referência/null no relatório final; silhouette isolada nunca cria uma persona ou segmento de ouvintes." )])
    return (stability,)


@app.cell
def _(mo, pca_frame, stability):
    best = stability.sort(["gate_ari", "ARI_mediana", "silhouette"], descending=True).head(1)
    mo.vstack([mo.md("## Evidence brief"), mo.ui.table(best), mo.md(f"A projeção mantém 2D como visão primária e limita a nuvem a {min(4_000, pca_frame.height):,} pontos. Uma visão 3D pode ser mantida como exploração opcional, mas não é necessária para o claim principal." )])
    return


if __name__ == "__main__":
    app.run()
