# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "duckdb>=1.1,<2", "marimo>=0.14,<1", "matplotlib>=3.9,<4",
#   "numpy>=2,<3", "pandas>=2.2,<4", "plotly>=5.24,<7", "polars>=1.20,<2",
#   "pyarrow>=18,<25", "scikit-learn>=1.5,<2", "statsmodels>=0.14,<1",
#   "wigglystuff>=0.5.21,<0.6",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full")


@app.cell
def _():
    from hashlib import sha256
    import sys
    from pathlib import Path
    from urllib.request import urlretrieve
    from zipfile import ZipFile

    repo_root = Path.cwd()
    bundle_path = repo_root / "spotify_molab_bundle.zip"
    if not (repo_root / "spotify_data").exists() and bundle_path.exists():
        with ZipFile(bundle_path) as bundle:
            bundle.extractall(repo_root)
    if not (repo_root / "spotify_data").exists():
        snapshot = "12f6f86d857b55ddd37ab0b1a575dfb49b7f3f36"
        snapshot_root = repo_root / f"desafio-01-{snapshot}"
        if not snapshot_root.exists():
            archive_path = repo_root / f"desafio-01-{snapshot}.zip"
            urlretrieve(f"https://github.com/d4vidz/desafio-01/archive/{snapshot}.zip", archive_path)
            with ZipFile(archive_path) as archive:
                archive.extractall(repo_root)
        repo_root = snapshot_root
    if not (repo_root / "spotify_data").exists():
        repo_root = Path(__file__).resolve().parents[1]
    csv_snapshot = repo_root / "data" / "raw" / "spotify_tracks.csv"
    expected_source = "1a769bbbbb2fa4451d4309248349799ce8ab5efc21e053e2bb3aa28ddcb53d83"
    if csv_snapshot.exists():
        observed_source = sha256(csv_snapshot.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if observed_source != expected_source:
            raise RuntimeError("O snapshot Molab não corresponde ao hash canônico do CSV.")
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
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
    from wigglystuff import ParallelCoordinates
    from spotify_data import (
        EvidenceStatus,
        NarrativeSection,
        build_data_layer,
        build_duckdb_layer,
        contract_capsule,
        deterministic_sample,
        load_tracks_raw,
        missing_identifier_counts,
        render_narrative_section,
    )
    return (EvidenceStatus, GroupShuffleSplit, HistGradientBoostingRegressor, KMeans, NarrativeSection, PCA,
            ParallelCoordinates, Path, ShuffleSplit, StandardScaler,
            build_data_layer, build_duckdb_layer, contract_capsule, calinski_harabasz_score, davies_bouldin_score,
            deterministic_sample, go, load_tracks_raw, mean_absolute_error, mean_squared_error,
            missing_identifier_counts, mo, np, pl, r2_score, render_narrative_section,
            repo_root, silhouette_score)


@app.cell
def _(Path, build_data_layer, load_tracks_raw, mo, repo_root):
    csv_path = repo_root / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    tracks_raw = load_tracks_raw(csv_path)
    layer = build_data_layer(csv_path)
    db = layer.connection
    report = layer.report
    tracks_clean = db.execute("SELECT * FROM tracks_clean").pl()
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    track_genres = db.execute("SELECT * FROM track_genres ORDER BY track_id, track_genre").pl()
    track_artists = db.execute("SELECT * FROM track_artists ORDER BY track_id, artist_position").pl()
    return csv_path, db, layer, report, track_artists, track_genres, tracks, tracks_clean, tracks_raw


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
def _(contract_capsule, missing_identifier_counts, pl, report, track_artists, track_genres, tracks, tracks_clean, tracks_raw):
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
    capsule = pl.DataFrame([contract_capsule(report)])
    return audit, capsule, contract, missing, ranges


@app.cell
def _(EvidenceStatus, NarrativeSection, audit, capsule, contract, missing, mo, ranges,
      render_narrative_section, report, tracks, tracks_clean, tracks_raw):
    _feature_columns = {
        "popularity", "duration_ms", "danceability", "energy", "key", "loudness",
        "mode", "speechiness", "acousticness", "instrumentalness", "liveness",
        "valence", "tempo", "time_signature",
    }
    _feature_missing = sum(
        item["missing_count"] for item in report.missingness
        if item["column"] in _feature_columns
    )
    _cleanup_summary = (
        f"`tracks_raw` preserva as {tracks_raw.height:,} linhas para auditoria. "
        f"`tracks_clean` remove {report.removals['missing_identifier_rows']:,} linha(s) sem identificação "
        f"e {report.removals['exact_duplicates']:,} duplicata(s) exata(s), além de aparar espaços externos. "
        f"As features e o target somam {_feature_missing:,} valores ausentes nesta execução; por isso nenhuma imputação real foi aplicada. "
        "Popularidade divergente é consolidada por mediana, preservando mínimo, máximo, contagem, amplitude e flag."
    ).replace(",", ".")
    _contract_narrative = NarrativeSection(
        title="Contrato e qualidade da camada de dados",
        question="A base está em condições de sustentar as análises sem esconder perdas, duplicidades ou conflitos?",
        population="O snapshot CSV completo e as relações reconstruídas em DuckDB",
        unit="uma linha física, uma faixa canônica ou uma aresta, conforme a tabela",
        method="Reconstruímos uma camada DuckDB efêmera e comparamos contagens, missingness, ranges, duplicatas, conflitos e grains.",
        how_to_read="Use a tabela de contrato para distinguir linhas físicas de faixas deduplicadas e arestas; leia os valores junto com seus denominadores.",
        denominator=f"{tracks_raw.height:,} linhas brutas; tabelas e contagens detalhadas abaixo.".replace(",", "."),
        result=f"A auditoria reporta {tracks_clean.height:,} linhas limpas e {tracks.height:,} faixas canônicas nesta execução.".replace(",", "."),
        interpretation="A camada é adequada para análises internas do snapshot, desde que cada notebook respeite o grain escolhido e explicite conflitos e limitações.",
        use="Servir como ponto de partida comum para todos os notebooks e para a auditoria de reprodutibilidade.",
        limitation="A proveniência externa permanece incompleta; isso limita claims sobre representatividade, causalidade e comportamento de ouvintes.",
        status=EvidenceStatus.INFRASTRUCTURE,
        terms={"Grain": "A unidade que cada linha representa; misturá-la pode duplicar contagens.", "Conflito": "O mesmo track_id aparece com valores divergentes que precisam ser sinalizados."},
    )
    mo.vstack([mo.md("## 1. Contrato e qualidade"), render_narrative_section(mo, _contract_narrative),
               mo.ui.table(capsule),
               mo.hstack([mo.ui.table(contract), mo.ui.table(audit)], widths="equal"),
               mo.md(_cleanup_summary),
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
def _(EvidenceStatus, NarrativeSection, fig_distribution, mo, render_narrative_section):
    _distribution_narrative = NarrativeSection(
        title="Distribuição de popularidade",
        question="Como a popularidade observada se distribui entre as faixas canônicas?",
        population="Faixas canônicas do snapshot", unit="uma faixa canônica",
        method="Um histograma agrupa os valores observados em intervalos para mostrar concentração, assimetria e caudas.",
        how_to_read="A altura indica o número de faixas em cada intervalo; não representa ouvintes nem evolução temporal.",
        denominator="Todas as faixas canônicas disponíveis na camada `tracks`.",
        result="A forma e as caudas descrevem este snapshot, com zeros e extremos preservados.",
        interpretation="Valores raros podem ser legítimos ou merecer sensibilidade; raridade isolada não prova erro de inserção.",
        use="Definir transformações e sensibilidades para as análises estatísticas posteriores.",
        limitation="O gráfico não identifica causalidade, viés de seleção ou tendência temporal.",
        status=EvidenceStatus.COMPLETE_EXPERIMENT,
        terms={"Outlier": "Observação extrema ou rara; não é automaticamente um erro."},
    )
    mo.vstack([mo.md("## 3. Distribuições e possíveis outliers"), render_narrative_section(mo, _distribution_narrative), fig_distribution,
               mo.md("Zeros são valores observados, não missingness. Extremos são sinalizados para investigação; não são removidos só por IQR, pois raridade e erro de inserção são conceitos diferentes.")])
    return


@app.cell
def _(features, mo):
    x_ctl = mo.ui.dropdown(features, value="energy", label="X")
    y_ctl = mo.ui.dropdown(features, value="danceability", label="Y")
    color_ctl = mo.ui.dropdown(["popularity", "genre_count", *features], value="popularity", label="Cor")
    return color_ctl, x_ctl, y_ctl


@app.cell
def _(color_ctl, deterministic_sample, go, tracks, x_ctl, y_ctl):
    rel = tracks.select(["track_id", "track_name", "artists", x_ctl.value, y_ctl.value, color_ctl.value]).drop_nulls()
    rel = deterministic_sample(rel, 4_000, seed=2026)
    fig_rel = go.Figure(go.Scattergl(x=rel[x_ctl.value].to_numpy(), y=rel[y_ctl.value].to_numpy(),
        mode="markers", marker={"size": 6, "opacity": .45, "color": rel[color_ctl.value].to_numpy(),
        "colorscale": "Viridis", "colorbar": {"title": color_ctl.value}},
        text=(rel["track_name"] + " — " + rel["artists"]).to_list(),
        hovertemplate="%{text}<br>x=%{x:.3f}<br>y=%{y:.3f}<extra></extra>"))
    fig_rel.update_layout(title=f"{x_ctl.value} × {y_ctl.value}", template="plotly_white", height=500)
    return fig_rel


@app.cell
def _(EvidenceStatus, NarrativeSection, color_ctl, fig_rel, mo, render_narrative_section, x_ctl, y_ctl):
    _relationship_narrative = NarrativeSection(
        title="Relação entre características musicais",
        question="Como duas características selecionadas variam conjuntamente no catálogo?",
        population="Amostra determinística de até 4.000 faixas canônicas",
        unit="uma faixa canônica representada por um ponto",
        method="Um scatter plot compara X e Y; a cor é uma terceira variável escolhida no controle.",
        how_to_read="Procure padrões gerais, concentração e pontos extremos; a cor ajuda a comparar uma dimensão, mas não prova mecanismo.",
        denominator="Até 4.000 pontos após remoção de nulos nas colunas selecionadas.",
        result=f"A visualização atual compara `{x_ctl.value}` com `{y_ctl.value}` e colore por `{color_ctl.value}`.",
        interpretation="Padrões visuais são hipóteses para testes estatísticos, não evidência confirmatória por si só.",
        use="Selecionar relações candidatas e sensibilidades para a análise de associações.",
        limitation="A amostragem é bounded e a cor não implica causalidade; os resultados dependem das variáveis escolhidas.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"Associação": "Variação conjunta observada, sem afirmar que uma variável causa a outra."},
    )
    mo.vstack([mo.md("## 4. Relações"), render_narrative_section(mo, _relationship_narrative), mo.hstack([x_ctl, y_ctl, color_ctl]), fig_rel,
               mo.md("Amostra determinística de até 4.000 faixas; cor não implica mecanismo causal.")])
    return


@app.cell
def _(ParallelCoordinates, deterministic_sample, mo, pl, tracks):
    pc = tracks.select(["track_id", "popularity", "danceability", "energy", "acousticness",
                        "instrumentalness", "valence", "genre_count"]).drop_nulls()
    pc = deterministic_sample(pc, 700, seed=2026).drop("track_id").with_columns(
        pl.when(pl.col("popularity") >= pl.col("popularity").quantile(.75))
        .then(pl.lit("quartil superior")).otherwise(pl.lit("demais")).alias("grupo"))
    parallel = mo.ui.anywidget(ParallelCoordinates(pc, color_by="grupo",
        color_map={"quartil superior": "#e76f51", "demais": "#277da1"}, height=500, width=0))
    parallel
    return


@app.cell
def _(KMeans, PCA, StandardScaler, calinski_harabasz_score, davies_bouldin_score,
      deterministic_sample, features, pl, silhouette_score, tracks):
    psrc = tracks.select(["track_id", "popularity", *features]).drop_nulls()
    psrc = deterministic_sample(psrc, 6_000, seed=2026)
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
def _(EvidenceStatus, NarrativeSection, best_k, cluster_metrics, go, mo, pframe, render_narrative_section, variance):
    fig_pca_2d = go.Figure(go.Scattergl(x=pframe["PC1"].to_numpy(), y=pframe["PC2"].to_numpy(),
        mode="markers", marker={"size": 5, "opacity": .45,
        "color": pframe["PC3"].to_numpy(), "colorscale": "Viridis", "colorbar": {"title": "PC3"}}))
    fig_pca_2d.update_layout(title="PCA 2D — visão primária", height=480, template="plotly_white")
    fig_pca = go.Figure(go.Scatter3d(x=pframe["PC1"].to_numpy(), y=pframe["PC2"].to_numpy(),
        z=pframe["PC3"].to_numpy(), mode="markers", marker={"size": 2.5, "opacity": .4,
        "color": pframe["cluster"].to_numpy(), "colorscale": "Turbo"}))
    fig_pca.update_layout(title=f"PCA 3D + KMeans opcional (k={best_k})", height=560)
    _structure_narrative = NarrativeSection(
        title="PCA e clustering do espaço de áudio",
        question="É possível resumir a geometria das audio features e encontrar agrupamentos estáveis?",
        population="Amostra determinística de até 6.000 faixas canônicas",
        unit="uma faixa representada por dez features contínuas padronizadas",
        method="PCA projeta as features em componentes; K-means é comparado para k entre 2 e 6 com métricas internas.",
        how_to_read="A distância no plano é geométrica; a variância explicada indica o que cada componente resume.",
        denominator="Até 6.000 faixas sem nulos nas dez features; k testado de 2 a 6.",
        result=f"A configuração escolhida pelo silhouette nesta exploração é k={best_k}; isso não constitui cluster natural validado.",
        interpretation="A projeção é útil para exploração de estrutura, mas estabilidade por bootstrap/null ainda é necessária antes de qualquer claim de segmentos.",
        use="Orientar o experimento independente de estrutura musical e suas sensibilidades.",
        limitation="Esta célula ainda não aplica o gate de estabilidade ARI nem a comparação com referência nula.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"PCA": "Projeção linear que organiza a variância das features em componentes.", "Silhouette": "Métrica interna de coesão e separação, não prova de clusters reais."},
    )
    mo.vstack([mo.md("## 5. PCA e clustering"), render_narrative_section(mo, _structure_narrative),
               mo.hstack([mo.ui.table(variance), mo.ui.table(cluster_metrics)], widths="equal"), fig_pca_2d, fig_pca,
               mo.md("A visão 2D é primária e a 3D é opcional/bounded. k maximiza silhouette entre 2–6, contrastado por Davies–Bouldin e Calinski–Harabasz. Clusters descrevem geometria; não são segmentos de ouvintes.")])
    return


@app.cell
def _(EvidenceStatus, NarrativeSection, db, go, mo, render_narrative_section):
    leaves = db.execute("""
      WITH genre_counts AS (SELECT track_id, count(DISTINCT track_genre) k_genre FROM track_genres GROUP BY 1),
      artist_counts AS (SELECT track_id, count(DISTINCT artist) k_artist FROM track_artists GROUP BY 1),
      top_genres AS (SELECT track_genre FROM track_genres GROUP BY 1 ORDER BY count(DISTINCT track_id) DESC, track_genre LIMIT 5),
      ranked_artists AS (
        SELECT tg.track_genre, ta.artist,
          row_number() OVER (PARTITION BY tg.track_genre ORDER BY count(DISTINCT tg.track_id) DESC, ta.artist) artist_rank
        FROM track_genres tg JOIN top_genres g USING(track_genre) JOIN track_artists ta USING(track_id)
        GROUP BY 1,2
      ), ranked_tracks AS (
        SELECT tg.track_genre, ta.artist, t.track_name, t.track_id, t.popularity,
          1.0/(gc.k_genre*ac.k_artist) AS area,
          row_number() OVER (PARTITION BY tg.track_genre,ta.artist ORDER BY t.popularity DESC,t.track_id) track_rank
        FROM track_genres tg JOIN ranked_artists ra USING(track_genre) JOIN track_artists ta USING(track_id)
        JOIN tracks t USING(track_id) JOIN genre_counts gc USING(track_id) JOIN artist_counts ac USING(track_id)
        WHERE ra.artist_rank <= 6 AND ta.artist=ra.artist
      ) SELECT * FROM ranked_tracks WHERE track_rank <= 8
      ORDER BY track_genre, artist, popularity DESC
    """).pl()
    tree_nodes = {"root": {"label": "catálogo selecionado", "parent": "", "value": float(leaves["area"].sum()), "color": 0.0}}
    for row in leaves.iter_rows(named=True):
        genre_id = f"g:{row['track_genre']}"
        artist_id = f"a:{row['track_genre']}|{row['artist']}"
        track_id = f"t:{row['track_genre']}|{row['artist']}|{row['track_id']}"
        tree_nodes.setdefault(genre_id, {"label": row["track_genre"], "parent": "root", "value": 0.0, "color": 0.0})
        tree_nodes.setdefault(artist_id, {"label": row["artist"], "parent": genre_id, "value": 0.0, "color": 0.0})
        tree_nodes[genre_id]["value"] += row["area"]
        tree_nodes[artist_id]["value"] += row["area"]
        tree_nodes[track_id] = {"label": row["track_name"][:42], "parent": artist_id, "value": row["area"], "color": row["popularity"]}
    tree = go.Figure(go.Treemap(ids=list(tree_nodes), labels=[x["label"] for x in tree_nodes.values()], parents=[x["parent"] for x in tree_nodes.values()], values=[x["value"] for x in tree_nodes.values()], branchvalues="total", marker={"colors": [x["color"] for x in tree_nodes.values()], "colorscale": "Viridis", "colorbar": {"title": "popularity"}}))
    tree.update_layout(title="Treemap: gênero → artista → faixa", height=560, template="plotly_white")
    _treemap_narrative = NarrativeSection(
        title="Treemap conectado: gênero → artista → faixa",
        question="Como uma seleção limitada do catálogo se distribui hierarquicamente entre gêneros, artistas e faixas?",
        population="Top 5 gêneros, 6 artistas por gênero e 8 faixas por artista",
        unit="uma faixa contribui fracionariamente para evitar dupla contagem em memberships",
        method="A hierarquia é derivada de arestas auditadas; área usa contribuição fracionária aditiva e cor usa popularity observada da folha.",
        how_to_read="Clique nos níveis para aprofundar; compare áreas como contribuição ao recorte, não como número bruto de ouvintes.",
        denominator="Até 5 × 6 × 8 folhas selecionadas, com pesos fracionários por gênero e artista.",
        result="A seleção conecta três entidades do catálogo sem tratar gênero como árvore taxonômica.",
        interpretation="A visualização ajuda a explorar concentração e interseções, mas não estima importância causal de artistas ou gêneros.",
        use="Avaliar se a hierarquia acrescenta narrativa ao relatório final.",
        limitation="O recorte top-n é exploratório e a área não é popularity; o parser de artistas ainda exige auditoria específica.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"Contribuição fracionária": "Peso 1/(n gêneros × n artistas) usado para reduzir duplicação no recorte."},
    )
    mo.vstack([mo.md("## 6. Treemap conectado e bounded"), render_narrative_section(mo, _treemap_narrative), tree,
               mo.md("Top 5 gêneros, 6 artistas/gênero e 8 faixas/artista. Área = contribuição aditiva `1/(n gêneros × n artistas)`; cor da folha = popularity observada. A visualização não trata gênero como árvore taxonômica nem usa popularity como área.")])
    return (tree,)


@app.cell
def _(db, go, np):
    overlap = db.execute("""WITH top AS (SELECT track_genre FROM track_genres GROUP BY 1
      ORDER BY count(DISTINCT track_id) DESC, track_genre LIMIT 15)
      SELECT a.track_genre s,b.track_genre t,count(DISTINCT a.track_id) w
      FROM track_genres a JOIN track_genres b USING(track_id)
      JOIN top x ON x.track_genre=a.track_genre JOIN top y ON y.track_genre=b.track_genre GROUP BY 1,2""").pl()
    names = sorted(set(overlap["s"].to_list())); lookup = {(r["s"],r["t"]):r["w"] for r in overlap.iter_rows(named=True)}
    matrix = np.array([[lookup.get((a,b),0) for b in names] for a in names])
    heatmap = go.Figure(go.Heatmap(z=matrix, x=names, y=names, colorscale="Blues"))
    heatmap.update_layout(title="Sobreposição dos 15 maiores gêneros", height=560)
    edges = db.execute("""SELECT ta.artist,tg.track_genre,count(DISTINCT tg.track_id) w
      FROM track_artists ta JOIN track_genres tg USING(track_id) GROUP BY 1,2 ORDER BY w DESC, ta.artist, tg.track_genre LIMIT 30""").pl()
    an = ["artista: "+x for x in sorted(set(edges["artist"].to_list()))]
    gn = ["gênero: "+x for x in sorted(set(edges["track_genre"].to_list()))]
    nodes=an+gn; ix={x:i for i,x in enumerate(nodes)}
    sankey=go.Figure(go.Sankey(node={"label":nodes},link={
      "source":[ix["artista: "+r["artist"]] for r in edges.iter_rows(named=True)],
      "target":[ix["gênero: "+r["track_genre"]] for r in edges.iter_rows(named=True)],"value":edges["w"].to_list()}))
    sankey.update_layout(title="30 maiores arestas artista–gênero",height=620)
    return heatmap, sankey


@app.cell
def _(EvidenceStatus, NarrativeSection, heatmap, mo, render_narrative_section, sankey):
    _graph_narrative = NarrativeSection(
        title="Grafos derivados de coocorrência",
        question="Quais gêneros compartilham faixas e quais conexões artista–gênero aparecem no recorte?",
        population="15 gêneros com maior suporte e 30 arestas artista–gênero mais frequentes",
        unit="uma aresta agregada entre entidades, ponderada por faixas distintas",
        method="Agregamos tabelas de arestas no DuckDB e exibimos uma matriz de sobreposição e um Sankey bounded.",
        how_to_read="Células mais intensas indicam mais faixas compartilhadas; links mais largos indicam maior peso no recorte.",
        denominator="Top 15 gêneros para a matriz e top 30 arestas para o Sankey.",
        result="As figuras mostram relações de catálogo observadas, não uma rede social de ouvintes.",
        interpretation="A estrutura é útil para formular hipóteses sobre gêneros relacionados e features de grafo.",
        use="Comparar, em experimento posterior, features de grafo contra o mesmo baseline e split.",
        limitation="Não há normalização Jaccard/cosseno nem validação incremental nesta exploração; nenhuma conclusão preditiva deve ser extraída.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"Coocorrência": "Duas categorias aparecem associadas à mesma faixa no snapshot."},
    )
    mo.vstack([mo.md("## 7. Grafos derivados — sem graph database"), render_narrative_section(mo, _graph_narrative), heatmap, sankey,
               mo.md("A matriz mostra faixas compartilhadas; o Sankey limitado revela hubs sem renderizar a rede completa.")])
    return


@app.cell
def _(GroupShuffleSplit, HistGradientBoostingRegressor, ShuffleSplit, db, deterministic_sample, features,
      mean_absolute_error, mean_squared_error, np, pl, r2_score, tracks):
    primary = db.execute("SELECT track_id,min_by(artist,artist_position) primary_artist FROM track_artists GROUP BY 1").pl()
    mf = tracks.select(["track_id","popularity","genre_count",*features]).join(primary,on="track_id").drop_nulls()
    mf = deterministic_sample(mf, 45_000, seed=2026)
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
def _(EvidenceStatus, NarrativeSection, go, mo, render_narrative_section, results, summary):
    _grouped_results=results.filter(results["split"]=="artista agrupado")
    fig=go.Figure()
    for name in sorted(_grouped_results["modelo"].unique().to_list()):
        fig.add_trace(go.Box(y=_grouped_results.filter(_grouped_results["modelo"]==name)["MAE"].to_list(),name=name,boxpoints="all"))
    fig.update_layout(title="MAE em cinco splits por artista",yaxis_title="MAE (menor é melhor)",height=440)
    _prediction_narrative = NarrativeSection(
      title="Protótipo exploratório de avaliação preditiva",
      question="Um conjunto de audio features reduz o erro de estimar a popularity observada para artistas não vistos?",
      population="Amostra bounded do snapshot, com split principal agrupado por artista",
      unit="uma faixa canônica com popularity observada",
      method="Comparamos uma baseline e um regressor em cinco divisões por artista; a divisão aleatória é apenas diagnóstico.",
      how_to_read="Compare distribuições de MAE: menor é melhor. Não interprete o gráfico como previsão temporal.",
      denominator="Cinco repetições do split agrupado; resumo com MAE, RMSE e R².",
      result="A tabela e o boxplot registram um experimento preliminar, ainda sem o protocolo completo de bootstrap e auditoria de fingerprints.",
      interpretation="O resultado pode orientar a próxima especificação, mas não sustenta claim preditivo final.",
      use="Servir como ponto de partida para a entrega de validação preditiva vinculada às issues #41 e #48.",
      limitation="Faltam modelos obrigatórios completos, intervalos pareados, estratos de colaboração e ablações fold-local; não alegar generalização validada.",
      status=EvidenceStatus.PROTOTYPE,
      terms={"Leakage": "Informação do teste ou do futuro que entra indevidamente no treino.", "MAE": "Erro absoluto médio em pontos de popularity; menor é melhor."},
    )
    mo.vstack([mo.md("## 8. Protótipos exploratórios — não validados"), render_narrative_section(mo, _prediction_narrative), mo.ui.table(summary),fig,
      mo.md("Target: popularidade contínua. Este bloco é um protótipo de desenho experimental; não apresenta resultados provisórios como evidência final." )])
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
