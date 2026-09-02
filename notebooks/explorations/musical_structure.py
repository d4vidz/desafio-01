import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path

    _repo_root = Path(__file__).resolve().parents[2]
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics import (calinski_harabasz_score, davies_bouldin_score,
                                 silhouette_score)
    from sklearn.preprocessing import StandardScaler
    from spotify_data import build_duckdb_layer

    return (KMeans, PCA, Path, StandardScaler, build_duckdb_layer,
            calinski_harabasz_score, davies_bouldin_score, go, mo, np, pl,
            silhouette_score)


@app.cell
def _(Path, build_duckdb_layer, mo):
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    db = build_duckdb_layer(csv_path)
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    track_genres = db.execute("SELECT track_id, track_genre FROM track_genres ORDER BY track_id, track_genre").pl()
    return csv_path, db, track_genres, tracks


@app.cell
def _(mo):
    mo.md("""
    # Musical structure: PCA e clustering exploratórios

    Este notebook é uma trilha independente para investigar a geometria do catálogo.
    Ele pode informar a análise de popularidade, mas não mede segmentos de ouvintes e
    não transforma clusters instáveis em personas.
    """)
    return


@app.cell
def _(mo, pl):
    features = [
        "danceability", "energy", "loudness", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo", "duration_ms",
    ]
    human_panel = [
        "danceability", "energy", "valence", "acousticness",
        "instrumentalness", "speechiness",
    ]
    feature_roles = pl.DataFrame({
        "papel": ["painel humano", "sensibilidade/contexto", "pool estrutural"],
        "features": [
            ", ".join(human_panel),
            "loudness, liveness, tempo, duration_ms",
            "todas as dez audio features",
        ],
        "uso": [
            "interpretação principal de associações com popularity",
            "sensibilidade e controle de redundância",
            "PCA, clustering e comparação de geometrias",
        ],
    })
    mo.vstack([
        mo.md("## 1. Papéis das features"),
        mo.ui.table(feature_roles),
        mo.md("O painel humano é uma decisão de foco, não uma remoção de colunas. A trilha estrutural usa as dez features contínuas para não impor uma narrativa de popularidade à geometria do catálogo."),
    ])
    return features, human_panel


@app.cell
def _(PCA, StandardScaler, features, pl, tracks):
    analysis_frame = tracks.select(["track_id", "representative_track_genre", *features]).drop_nulls()
    analysis_frame = analysis_frame.sample(n=min(20_000, analysis_frame.height), seed=2026)
    scaled = StandardScaler().fit_transform(analysis_frame.select(features).to_numpy())
    pca = PCA(n_components=3, random_state=2026)
    components = pca.fit_transform(scaled)
    pca_frame = analysis_frame.select(["track_id", "representative_track_genre"]).with_columns(
        pl.Series("PC1", components[:, 0]),
        pl.Series("PC2", components[:, 1]),
        pl.Series("PC3", components[:, 2]),
    )
    variance = pl.DataFrame({
        "componente": ["PC1", "PC2", "PC3"],
        "variância_explicada": pca.explained_variance_ratio_,
    }).with_columns(pl.col("variância_explicada").round(4))
    loadings = pl.DataFrame({
        "feature": features,
        "PC1": pca.components_[0],
        "PC2": pca.components_[1],
        "PC3": pca.components_[2],
    }).with_columns(pl.all().exclude("feature").round(3))
    return analysis_frame, loadings, pca_frame, variance


@app.cell
def _(go, loadings, mo, pca_frame, variance):
    plot_frame = pca_frame.sample(n=min(6_000, pca_frame.height), seed=2026)
    fig = go.Figure(go.Scattergl(
        x=plot_frame["PC1"].to_numpy(),
        y=plot_frame["PC2"].to_numpy(),
        mode="markers",
        marker={"size": 5, "opacity": 0.45, "color": plot_frame["PC3"].to_numpy(), "colorscale": "Viridis", "colorbar": {"title": "PC3"}},
        text=plot_frame["representative_track_genre"].to_list(),
        hovertemplate="gênero=%{text}<br>PC1=%{x:.2f}<br>PC2=%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(title="Projeção PCA: PC1 × PC2, cor por PC3", template="plotly_white", height=560)
    mo.vstack([
        mo.md("## 2. PCA"),
        mo.hstack([mo.ui.table(variance), mo.ui.table(loadings)], widths="equal"),
        fig,
        mo.md("A figura mostra uma amostra bounded de até 6.000 faixas. Loadings e variância são necessários para interpretar qualquer eixo; uma nuvem visualmente contínua não implica ausência de estrutura relevante."),
    ])
    return


@app.cell
def _(KMeans, analysis_frame, calinski_harabasz_score, davies_bouldin_score,
      features, np, pl, silhouette_score):
    matrix = analysis_frame.select(features).to_numpy()
    cluster_rows = []
    labels_by_k = {}
    for k in range(2, 7):
        labels = KMeans(n_clusters=k, n_init=10, random_state=2026).fit_predict(matrix)
        labels_by_k[k] = labels
        cluster_rows.append({
            "k": k,
            "silhouette": silhouette_score(matrix, labels, sample_size=min(5_000, len(labels)), random_state=2026),
            "davies_bouldin": davies_bouldin_score(matrix, labels),
            "calinski_harabasz": calinski_harabasz_score(matrix, labels),
        })
    cluster_metrics = pl.DataFrame(cluster_rows).with_columns(pl.all().exclude("k").round(3))
    best_k = int(cluster_metrics.sort("silhouette", descending=True)[0, "k"])
    clustered = analysis_frame.select(["track_id", "representative_track_genre"]).with_columns(
        pl.Series("cluster", labels_by_k[best_k]),
    )
    cluster_profile = analysis_frame.with_columns(
        pl.Series("cluster", labels_by_k[best_k]),
    ).group_by("cluster").agg(
        pl.len().alias("faixas"),
        *[pl.col(feature).mean().alias(feature) for feature in features],
    ).sort("cluster").with_columns(pl.all().exclude(["cluster", "faixas"]).round(3))
    return best_k, cluster_metrics, cluster_profile, clustered


@app.cell
def _(best_k, cluster_metrics, cluster_profile, mo):
    mo.vstack([
        mo.md(f"## 3. Clustering exploratório — k selecionado provisoriamente: {best_k}"),
        mo.ui.table(cluster_metrics),
        mo.ui.table(cluster_profile),
        mo.md("Silhouette é apenas um critério entre vários. A escolha de k é provisória e deve ser comparada com estabilidade por resampling, outros algoritmos e loadings da PCA. Não nomear estes grupos como segmentos de público."),
    ])
    return


@app.cell
def _(clustered, mo, pl, track_genres):
    genre_cluster = (
        track_genres.join(clustered.select(["track_id", "cluster"]), on="track_id", how="inner")
        .group_by(["track_genre", "cluster"])
        .len()
        .rename({"len": "faixas"})
        .sort("faixas", descending=True)
        .head(30)
    )
    mo.vstack([
        mo.md("## 4. Relação dos clusters com gênero"),
        mo.ui.table(genre_cluster),
        mo.md("Gênero aparece como contexto pós-hoc. A mesma faixa pode contribuir para mais de um gênero; por isso esta tabela não deve ser lida como uma distribuição independente de faixas."),
    ])
    return genre_cluster


@app.cell
def _(best_k, loadings, mo, pl, variance):
    top_loading = loadings.with_columns(
        pl.max_horizontal(pl.col("PC1").abs(), pl.col("PC2").abs(), pl.col("PC3").abs()).alias("maior_loading")
    ).sort("maior_loading", descending=True).head(5)
    evidence_brief = mo.md(f"""
    ## 5. Evidence brief

    - O notebook usa até 20.000 faixas, seed fixa e dez audio features padronizadas.
    - Os três primeiros componentes explicam, respectivamente, {variance[0, 'variância_explicada']:.3f}, {variance[1, 'variância_explicada']:.3f} e {variance[2, 'variância_explicada']:.3f} da variância desta amostra.
    - O melhor k entre 2 e 6 por silhouette é {best_k}; isso é uma escolha exploratória, não evidência de clusters naturais.
    - A leitura recomendada para a trilha de popularity é usar loadings, estabilidade e heterogeneidade por gênero como hipóteses, nunca como perfis de ouvintes.
    """)
    mo.vstack([evidence_brief, mo.ui.table(top_loading)])
    return


if __name__ == "__main__":
    app.run()
