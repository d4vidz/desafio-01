import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path
    _repo_root = Path(__file__).resolve().parents[1]
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import (calinski_harabasz_score, davies_bouldin_score,
                                 mean_absolute_error, mean_squared_error, r2_score,
                                 silhouette_score)
    from sklearn.model_selection import GroupShuffleSplit, ShuffleSplit
    from sklearn.preprocessing import StandardScaler
    from wigglystuff import ParallelCoordinates, Treemap
    from spotify_data import build_duckdb_layer, load_tracks_raw, missing_identifier_counts
    return (GroupShuffleSplit, HistGradientBoostingRegressor, KMeans, PCA,
            ParallelCoordinates, Path, ShuffleSplit, StandardScaler, Treemap,
            build_duckdb_layer, calinski_harabasz_score, davies_bouldin_score,
            go, load_tracks_raw, mean_absolute_error, mean_squared_error,
            missing_identifier_counts, mo, np, pl, r2_score, silhouette_score)


@app.cell
def _(Path, build_duckdb_layer, load_tracks_raw, mo):
    csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    tracks_raw = load_tracks_raw(csv_path)
    db = build_duckdb_layer(csv_path)
    tracks_clean = db.execute("SELECT * FROM tracks_clean").pl()
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    track_genres = db.execute("SELECT * FROM track_genres ORDER BY track_id, track_genre").pl()
    track_artists = db.execute("SELECT * FROM track_artists ORDER BY track_id, artist_position").pl()
    return csv_path, db, track_artists, track_genres, tracks, tracks_clean, tracks_raw


@app.cell
def _(mo):
    mo.md("""
    # Spotify: do contrato de dados à evidência
    O CSV versionado é a fonte; DuckDB é reconstruído **em memória** e entrega frames Polars
    limitados às visualizações. Pergunta orientadora: **quais relações descritivas e preditivas
    são sustentadas pelo catálogo, sem confundir associação com causalidade?**
    """)
    return


@app.cell
def _(missing_identifier_counts, pl, track_artists, track_genres, tracks, tracks_clean, tracks_raw):
    contract = pl.DataFrame({
        "relação": ["tracks_raw", "tracks_clean", "tracks", "track_genres", "track_artists"],
        "linhas": [tracks_raw.height, tracks_clean.height, tracks.height, track_genres.height, track_artists.height],
        "grain": ["linha física do CSV", "linha limpa", "track_id", "track_id × gênero", "track_id × artista"],
    })
    missing = missing_identifier_counts(tracks_raw).filter(pl.col("missing_count") > 0)
    audit = pl.DataFrame({
        "métrica": ["linhas brutas", "linhas limpas", "faixas", "track_id repetidos", "duplicatas físicas removidas",
                    "faixas multigênero", "conflitos de popularidade"],
        "valor": [tracks_raw.height, tracks_clean.height, tracks.height,
                  tracks_raw.group_by("track_id").len().filter(pl.col("len") > 1).height,
                  tracks_raw.height - 1 - tracks_clean.height,
                  tracks.filter(pl.col("genre_count") > 1).height,
                  tracks.filter(pl.col("popularity_conflict")).height],
    })
    ranges = pl.DataFrame({
        "regra": ["popularidade fora de [0,100]", "duration_ms <= 0", "tempo <= 0"],
        "linhas": [tracks_raw.filter(~pl.col("popularity").is_between(0, 100)).height,
                   tracks_raw.filter(pl.col("duration_ms") <= 0).height,
                   tracks_raw.filter(pl.col("tempo") <= 0).height],
    })
    return audit, contract, missing, ranges


@app.cell
def _(audit, contract, missing, mo, ranges):
    mo.vstack([mo.md("## 1. Contrato e qualidade"),
               mo.hstack([mo.ui.table(contract), mo.ui.table(audit)], widths="equal"),
               mo.md("`tracks_raw` preserva as 114.000 linhas para auditoria. `tracks_clean` reproduz a limpeza revisada: remove a linha sem identificação textual, o índice exportado e 450 duplicatas exatas, além de aparar espaços externos. Há **zero missingness numérico**: imputação inventaria um experimento sem objeto. Popularidade divergente é consolidada por mediana, preservando mínimo, máximo, contagem, amplitude e flag."),
               mo.hstack([mo.ui.table(missing), mo.ui.table(ranges)], widths="equal")])
    return


@app.cell
def _(go, pl, tracks):
    features = ["danceability", "energy", "loudness", "speechiness", "acousticness",
                "instrumentalness", "liveness", "valence", "tempo", "duration_ms"]
    human_features = ["danceability", "energy", "valence", "acousticness", "instrumentalness", "speechiness"]
    feature_roles = pl.DataFrame({
        "papel": ["painel humano", "sensibilidade/contexto", "categóricas/contexto", "pool automatizado"],
        "colunas": [
            ", ".join(human_features),
            "loudness, liveness, tempo, duration_ms",
            "explicit, key, mode, time_signature, gênero e artista",
            "todas as audio features e categóricas válidas, sem popularity ou IDs",
        ],
        "regra": [
            "associações e comparações principais",
            "sensibilidade, redundância e experimentos secundários",
            "análises próprias e agrupamento; não correlação contínua silenciosa",
            "seleção regularizada, importance e estabilidade held-out",
        ],
    })
    fig_distribution = go.Figure(go.Histogram(x=tracks["popularity"].to_numpy(), nbinsx=40))
    fig_distribution.update_layout(title="Popularidade canônica por faixa", xaxis_title="popularidade",
                                   yaxis_title="faixas", template="plotly_white", height=420)
    return feature_roles, features, fig_distribution, human_features


@app.cell
def _(feature_roles, mo):
    mo.vstack([
        mo.md("## 2. Papéis das features e foco do primeiro ciclo"),
        mo.ui.table(feature_roles),
        mo.md("O painel humano é um foco interpretativo v0.1, não uma remoção de colunas. O pool automatizado permanece mais amplo e deve respeitar os splits e a disponibilidade de cada feature."),
    ])
    return


@app.cell
def _(fig_distribution, mo):
    mo.vstack([mo.md("## 3. Distribuições e possíveis outliers"), fig_distribution,
               mo.md("Zeros são valores observados, não missingness. Extremos são sinalizados para investigação; não são removidos só por IQR, pois raridade e erro de inserção são conceitos diferentes.")])
    return


@app.cell
def _(features, mo):
    x_ctl = mo.ui.dropdown(features, value="energy", label="X")
    y_ctl = mo.ui.dropdown(features, value="danceability", label="Y")
    color_ctl = mo.ui.dropdown(["popularity", "genre_count", *features], value="popularity", label="Cor")
    return color_ctl, x_ctl, y_ctl


@app.cell
def _(color_ctl, go, tracks, x_ctl, y_ctl):
    rel = tracks.select(["track_name", "artists", x_ctl.value, y_ctl.value, color_ctl.value]).drop_nulls()
    rel = rel.sample(n=min(4_000, rel.height), seed=2026)
    fig_rel = go.Figure(go.Scattergl(x=rel[x_ctl.value].to_numpy(), y=rel[y_ctl.value].to_numpy(),
        mode="markers", marker={"size": 6, "opacity": .45, "color": rel[color_ctl.value].to_numpy(),
        "colorscale": "Viridis", "colorbar": {"title": color_ctl.value}},
        text=(rel["track_name"] + " — " + rel["artists"]).to_list(),
        hovertemplate="%{text}<br>x=%{x:.3f}<br>y=%{y:.3f}<extra></extra>"))
    fig_rel.update_layout(title=f"{x_ctl.value} × {y_ctl.value}", template="plotly_white", height=500)
    return fig_rel


@app.cell
def _(color_ctl, fig_rel, mo, x_ctl, y_ctl):
    mo.vstack([mo.md("## 4. Relações"), mo.hstack([x_ctl, y_ctl, color_ctl]), fig_rel,
               mo.md("Amostra determinística de até 4.000 faixas; cor não implica mecanismo causal.")])
    return


@app.cell
def _(ParallelCoordinates, mo, pl, tracks):
    pc = tracks.select(["popularity", "danceability", "energy", "acousticness",
                        "instrumentalness", "valence", "genre_count"]).drop_nulls()
    pc = pc.sample(n=min(700, pc.height), seed=2026).with_columns(
        pl.when(pl.col("popularity") >= pl.col("popularity").quantile(.75))
        .then(pl.lit("quartil superior")).otherwise(pl.lit("demais")).alias("grupo"))
    parallel = mo.ui.anywidget(ParallelCoordinates(pc, color_by="grupo",
        color_map={"quartil superior": "#e76f51", "demais": "#277da1"}, height=500, width=0))
    parallel
    return


@app.cell
def _(KMeans, PCA, StandardScaler, calinski_harabasz_score, davies_bouldin_score,
      features, pl, silhouette_score, tracks):
    psrc = tracks.select(["track_id", "popularity", *features]).drop_nulls()
    psrc = psrc.sample(n=min(20_000, psrc.height), seed=2026)
    scaled = StandardScaler().fit_transform(psrc.select(features).to_numpy())
    pca = PCA(n_components=3, random_state=2026)
    pcs = pca.fit_transform(scaled)
    _cluster_rows, labels_by_k = [], {}
    for k in range(2, 7):
        labels = KMeans(n_clusters=k, n_init=10, random_state=2026).fit_predict(scaled)
        labels_by_k[k] = labels
        _cluster_rows.append({"k": k, "silhouette": silhouette_score(scaled, labels, sample_size=5_000, random_state=2026),
                     "davies_bouldin": davies_bouldin_score(scaled, labels),
                     "calinski_harabasz": calinski_harabasz_score(scaled, labels)})
    cluster_metrics = pl.DataFrame(_cluster_rows).with_columns(pl.all().exclude("k").round(3))
    best_k = int(cluster_metrics.sort("silhouette", descending=True)[0, "k"])
    pframe = psrc.with_columns(pl.Series("PC1", pcs[:, 0]), pl.Series("PC2", pcs[:, 1]),
                              pl.Series("PC3", pcs[:, 2]), pl.Series("cluster", labels_by_k[best_k]))
    variance = pl.DataFrame({"PC": [1, 2, 3], "variância_explicada": pca.explained_variance_ratio_})
    return best_k, cluster_metrics, pframe, variance


@app.cell
def _(best_k, cluster_metrics, go, mo, pframe, variance):
    fig_pca = go.Figure(go.Scatter3d(x=pframe["PC1"].to_numpy(), y=pframe["PC2"].to_numpy(),
        z=pframe["PC3"].to_numpy(), mode="markers", marker={"size": 2.5, "opacity": .4,
        "color": pframe["cluster"].to_numpy(), "colorscale": "Turbo"}))
    fig_pca.update_layout(title=f"PCA 3D + KMeans exploratório (k={best_k})", height=600)
    mo.vstack([mo.md("## 5. PCA e clustering"),
               mo.hstack([mo.ui.table(variance), mo.ui.table(cluster_metrics)], widths="equal"), fig_pca,
               mo.md("k maximiza silhouette entre 2–6, contrastado por Davies–Bouldin e Calinski–Harabasz. Clusters descrevem geometria; não são segmentos de ouvintes.")])
    return


@app.cell
def _(Treemap, db, mo):
    leaves = db.execute("""
      WITH g AS (SELECT track_genre, dense_rank() OVER (ORDER BY count(DISTINCT track_id) DESC) rg
        FROM track_genres GROUP BY 1),
      a AS (SELECT tg.track_genre, ta.artist, dense_rank() OVER
        (PARTITION BY tg.track_genre ORDER BY count(DISTINCT tg.track_id) DESC) ra
        FROM track_genres tg JOIN track_artists ta USING(track_id) JOIN g USING(track_genre)
        WHERE rg<=5 GROUP BY 1,2),
      x AS (SELECT tg.track_genre, ta.artist, t.track_name, t.track_id, t.popularity,
        row_number() OVER (PARTITION BY tg.track_genre,ta.artist ORDER BY t.popularity DESC,t.track_id) rt
        FROM track_genres tg JOIN track_artists ta USING(track_id) JOIN tracks t USING(track_id)
        JOIN a ON a.track_genre=tg.track_genre AND a.artist=ta.artist WHERE a.ra<=6)
      SELECT * FROM x WHERE rt<=8 ORDER BY 1,2,5 DESC""").pl()
    paths = {f"{r['track_genre']} › {r['artist']} › {r['track_name']} [{r['track_id'][:6]}]":
             max(float(r["popularity"]), 1) for r in leaves.iter_rows(named=True)}
    tree = mo.ui.anywidget(Treemap.from_paths(paths, sep=" › ", root_name="catálogo selecionado",
                                              width="100%", height=560, max_depth=3))
    mo.vstack([mo.md("## 6. Treemap: gênero → artista → faixa"), tree,
               mo.md("Top 5 gêneros, 6 artistas/gênero e 8 faixas/artista. Área = popularidade (mínimo visual 1); cor = ramo hierárquico. A mesma faixa pode pertencer a múltiplos gêneros.")])
    return


@app.cell
def _(db, go, np):
    overlap = db.execute("""WITH top AS (SELECT track_genre FROM track_genres GROUP BY 1
      ORDER BY count(DISTINCT track_id) DESC LIMIT 15)
      SELECT a.track_genre s,b.track_genre t,count(DISTINCT a.track_id) w
      FROM track_genres a JOIN track_genres b USING(track_id)
      JOIN top x ON x.track_genre=a.track_genre JOIN top y ON y.track_genre=b.track_genre GROUP BY 1,2""").pl()
    names = sorted(set(overlap["s"].to_list())); lookup = {(r["s"],r["t"]):r["w"] for r in overlap.iter_rows(named=True)}
    matrix = np.array([[lookup.get((a,b),0) for b in names] for a in names])
    heatmap = go.Figure(go.Heatmap(z=matrix, x=names, y=names, colorscale="Blues"))
    heatmap.update_layout(title="Sobreposição dos 15 maiores gêneros", height=560)
    edges = db.execute("""SELECT ta.artist,tg.track_genre,count(DISTINCT tg.track_id) w
      FROM track_artists ta JOIN track_genres tg USING(track_id) GROUP BY 1,2 ORDER BY w DESC LIMIT 30""").pl()
    an = ["artista: "+x for x in sorted(set(edges["artist"].to_list()))]
    gn = ["gênero: "+x for x in sorted(set(edges["track_genre"].to_list()))]
    nodes=an+gn; ix={x:i for i,x in enumerate(nodes)}
    sankey=go.Figure(go.Sankey(node={"label":nodes},link={
      "source":[ix["artista: "+r["artist"]] for r in edges.iter_rows(named=True)],
      "target":[ix["gênero: "+r["track_genre"]] for r in edges.iter_rows(named=True)],"value":edges["w"].to_list()}))
    sankey.update_layout(title="30 maiores arestas artista–gênero",height=620)
    return heatmap, sankey


@app.cell
def _(heatmap, mo, sankey):
    mo.vstack([mo.md("## 7. Grafos derivados — sem graph database"), heatmap, sankey,
               mo.md("A matriz mostra faixas compartilhadas; o Sankey limitado revela hubs sem renderizar a rede completa.")])
    return


@app.cell
def _(GroupShuffleSplit, HistGradientBoostingRegressor, ShuffleSplit, db, features,
      mean_absolute_error, mean_squared_error, np, pl, r2_score, tracks):
    primary = db.execute("SELECT track_id,min_by(artist,artist_position) primary_artist FROM track_artists GROUP BY 1").pl()
    mf = tracks.select(["track_id","popularity","genre_count",*features]).join(primary,on="track_id").drop_nulls()
    mf = mf.sample(n=min(45_000,mf.height),seed=2026)
    def evaluate(train_i,test_i,split,repeat):
        train,test=mf[train_i],mf[test_i]
        stats=train.group_by("primary_artist").agg(pl.len().alias("artist_catalogue_size"))
        train=train.join(stats,on="primary_artist"); test=test.join(stats,on="primary_artist",how="left").with_columns(pl.col("artist_catalogue_size").fill_null(0))
        yt,yv=train["popularity"].to_numpy(),test["popularity"].to_numpy()
        preds={"baseline_mediana":np.full(len(yv),np.median(yt))}
        for name,cols in {"audio":features,"audio+grafo":[*features,"genre_count","artist_catalogue_size"]}.items():
            model=HistGradientBoostingRegressor(max_iter=140,max_leaf_nodes=24,random_state=2026)
            model.fit(train.select(cols).to_numpy(),yt); preds[name]=model.predict(test.select(cols).to_numpy())
        return [{"split":split,"repetição":repeat,"modelo":n,"MAE":mean_absolute_error(yv,p),
                 "RMSE":mean_squared_error(yv,p)**.5,"R2":r2_score(yv,p)} for n,p in preds.items()]
    _model_rows=[]
    _grouped_split=GroupShuffleSplit(n_splits=5,test_size=.2,random_state=2026)
    for i,(a,b) in enumerate(_grouped_split.split(mf,groups=mf["primary_artist"].to_numpy()),1): _model_rows+=evaluate(a,b,"artista agrupado",i)
    for a,b in ShuffleSplit(n_splits=1,test_size=.2,random_state=2026).split(mf): _model_rows+=evaluate(a,b,"aleatório (diagnóstico)",1)
    results=pl.DataFrame(_model_rows)
    summary=results.group_by(["split","modelo"]).agg(pl.mean("MAE").alias("MAE_média"),
      pl.quantile("MAE",.1).alias("MAE_p10"),pl.quantile("MAE",.9).alias("MAE_p90"),
      pl.mean("RMSE").alias("RMSE_média"),pl.mean("R2").alias("R2_médio")).sort(["split","MAE_média"]).with_columns(pl.all().exclude(["split","modelo"]).round(3))
    return results, summary


@app.cell
def _(go, mo, results, summary):
    _grouped_results=results.filter(results["split"]=="artista agrupado")
    fig=go.Figure()
    for name in sorted(_grouped_results["modelo"].unique().to_list()):
        fig.add_trace(go.Box(y=_grouped_results.filter(_grouped_results["modelo"]==name)["MAE"].to_list(),name=name,boxpoints="all"))
    fig.update_layout(title="MAE em cinco splits por artista",yaxis_title="MAE (menor é melhor)",height=440)
    mo.vstack([mo.md("## 8. Experimento preditivo validado"),mo.ui.table(summary),fig,
      mo.md("Target: popularidade contínua. Split principal agrupa artistas; aleatório é diagnóstico. `audio+grafo` adiciona número de gêneros e tamanho do catálogo do artista calculado só no treino. Ganho instável é resultado inconclusivo.")])
    return


@app.cell
def _(mo, pl):
    scorecard=pl.DataFrame({"frente":["qualidade","EDA","clustering","grafos","predição"],
      "claim permitido":["descrever conflitos","associação no catálogo","geometria exploratória","sobreposição/hubs","generalização a artistas não vistos"],
      "não alegar":["ausência de viés","causalidade","segmentos naturais","influência social","próximo hit"]})
    mo.vstack([mo.md("## 9. Scorecard e próximos caminhos"),mo.ui.table(scorecard),mo.md("""
    - Quais relações persistem dentro de gênero?
    - A massa de popularidade zero varia por gênero, artista ou conflito de duplicação?
    - Clusters são estáveis a seed, amostra e algoritmo?
    - Quais overlaps permanecem após normalização Jaccard/cosseno?
    - Features de grafo melhoram consistentemente o held-out por artista?
    - Como definições globais e intragênero de “alta popularidade” mudam a leitura?

    O lock de claims deve seguir este scorecard, não o gráfico mais chamativo.
    """)])
    return


if __name__ == "__main__":
    app.run()
