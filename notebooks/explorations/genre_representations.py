"""Representações de gênero: multi-hot, PPMI/SVD e perfis de áudio."""

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path
    from zipfile import ZipFile

    root = Path.cwd()
    bundle_path = root / "spotify_molab_bundle.zip"
    if not (root / "spotify_data").exists() and bundle_path.exists():
        with ZipFile(bundle_path) as bundle:
            bundle.extractall(root)
    if not (root / "spotify_data").exists():
        root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    from spotify_data import (CONTINUOUS_AUDIO_FEATURES, build_data_layer,
                              fit_genre_ppmi, genre_audio_profiles,
                              genre_membership_matrix, robust_pca_profiles,
                              EvidenceStatus, NarrativeSection,
                              render_narrative_section)
    return CONTINUOUS_AUDIO_FEATURES, EvidenceStatus, NarrativeSection, Path, build_data_layer, fit_genre_ppmi, genre_audio_profiles, genre_membership_matrix, go, mo, np, pl, render_narrative_section, robust_pca_profiles, root


@app.cell
def _(Path, build_data_layer, mo, root):
    csv_path = root / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    genres = db.execute("SELECT * FROM track_genres ORDER BY track_id, track_genre").pl()
    artists = db.execute("SELECT * FROM track_artists ORDER BY track_id, artist_position").pl()
    return artists, db, genres, layer, tracks


@app.cell
def _(EvidenceStatus, NarrativeSection, genres, mo, pl, render_narrative_section, tracks):
    support = genres.group_by("track_genre").agg(
        pl.col("track_id").n_unique().alias("faixas"),
        pl.len().alias("memberships"),
    )
    support = support.with_columns((pl.col("faixas") < 300).alias("aviso_esparsidade")).sort("faixas", descending=True)
    multi = tracks.filter(pl.col("genre_count") > 1).height
    support_narrative = NarrativeSection(
        title="Mapa de suporte das representações",
        question="Quantas faixas e relações faixa–gênero sustentam cada representação?",
        population=f"{tracks.height:,} faixas canônicas e {genres.height:,} arestas faixa–gênero no snapshot.",
        unit="uma aresta faixa–gênero; faixas distintas são contadas separadamente",
        method="Agrupamos a tabela de arestas por gênero e contamos faixas distintas e arestas.",
        how_to_read="Use `faixas` para o tamanho do catálogo e `memberships` para o volume de relações.",
        denominator=f"O aviso marca gêneros com menos de 300 faixas; há {multi:,} faixas multigênero.",
        result=f"O snapshot contém {support.height} gêneros; os maiores suportes estão na tabela.",
        interpretation="Separar faixas de memberships torna a sobreposição de gêneros auditável.",
        use="O suporte orienta filtros, pooling e avisos de esparsidade.",
        limitation="O limite de 300 faixas é operacional para inferência, não uma avaliação de qualidade musical.",
        status=EvidenceStatus.INFRASTRUCTURE,
        terms={"membership": "relação explícita entre uma faixa e um gênero"},
    )
    mo.vstack([
        mo.md("# Representações de gênero e relações conectadas"),
        render_narrative_section(mo, support_narrative),
        mo.ui.table(support.head(20)),
    ])
    return (support,)


@app.cell
def _(EvidenceStatus, NarrativeSection, fit_genre_ppmi, genre_membership_matrix, genres, mo, np, pl, render_narrative_section, tracks):
    ids = tracks["track_id"].to_list()
    multi_hot, vocabulary = genre_membership_matrix(genres, ids)
    embedding = fit_genre_ppmi(genres, ids, n_components=8)
    embeddings = embedding.transform(genres, ids).filter(pl.col("track_id").is_in(ids[:3000]))
    overview = pl.DataFrame({
        "representacao": ["sem gênero", "multi-hot", "PPMI + TruncatedSVD"],
        "dimensoes": [0, len(vocabulary), 8],
        "ajuste": ["baseline", "vocabulário do treino", "coocorrência; fold-local em predição"],
    })
    ladder_narrative = NarrativeSection(
        title="Escada de representações de gênero",
        question="Uma representação que conhece gênero melhora a descrição das faixas?",
        population=f"As {tracks.height:,} faixas canônicas e seus gêneros declarados; esta demonstração usa o snapshot completo apenas para exploração.",
        unit="uma linha por faixa e uma coluna por gênero conhecido",
        method="Comparamos ausência de gênero, indicadores multi-hot e um embedding PPMI reduzido por TruncatedSVD. PPMI destaca coocorrências surpreendentes; SVD comprime a matriz.",
        how_to_read="Proximidade no embedding significa coocorrência de gêneros, não semelhança sonora nem causalidade.",
        denominator=f"Vocabulário de {len(vocabulary)} gêneros; dimensão primária {embedding.n_components}D; 3.000 faixas aparecem na tabela.",
        result=f"A escada produz três alternativas, incluindo {embedding.n_components} dimensões no embedding.",
        interpretation="O embedding é uma hipótese compacta sobre relações de gênero, não evidência de ganho preditivo nesta etapa.",
        use="A comparação será repetida fold-localmente em #32/#50.",
        limitation="OOV recebe vetor zero e faixas multigênero recebem a média; o ajuste usa o snapshot inteiro e não é validação fora da amostra.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"OOV": "gênero ausente no vocabulário aprendido", "multi-hot": "vetor de indicadores 0/1 para presença de gêneros"},
    )
    mo.vstack([
        mo.md("## 1. Ladder obrigatório"),
        render_narrative_section(mo, ladder_narrative),
        mo.ui.table(overview),
        mo.ui.table(embeddings.head(8).with_columns(pl.all().exclude("track_id").round(3))),
    ])
    return embedding, embeddings, multi_hot, overview, vocabulary


@app.cell
def _(EvidenceStatus, NarrativeSection, genre_audio_profiles, genres, mo, pl, render_narrative_section, robust_pca_profiles, tracks):
    profiles = genre_audio_profiles(tracks, genres)
    coordinates, pca = robust_pca_profiles(profiles)
    profile_table = profiles.join(coordinates, on="track_genre").head(20)
    profiles_narrative = NarrativeSection(
        title="Perfis de áudio por gênero",
        question="Como os gêneros diferem quando resumimos suas distribuições de áudio?",
        population=f"{genres.height:,} memberships ligadas às faixas; o perfil primário usa todas as memberships.",
        unit="um perfil agregado por gênero, com dez features e cinco quantis por feature",
        method="Calculamos quantis 10, 25, 50, 75 e 90 e aplicamos RobustScaler e PCA aos perfis.",
        how_to_read="Pontos próximos têm perfis agregados parecidos, não necessariamente as mesmas faixas.",
        denominator=f"{profiles.height} gêneros perfilados; a tabela mostra 20.",
        result="A tabela expõe quantis e coordenadas que auditam a posição no gráfico.",
        interpretation="Esta é uma descrição comparativa de catálogos por gênero, não uma prova de clusters naturais.",
        use="Os perfis serão comparados a vizinhanças de coocorrência em #32.",
        limitation="Sensibilidades por gênero único e peso 1/k ainda não foram executadas.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"quantil": "posição na distribuição, como a mediana (q50)", "RobustScaler": "escala baseada em mediana e intervalo interquartil"},
    )
    mo.vstack([
        mo.md("## 2. Perfil de áudio por gênero"),
        render_narrative_section(mo, profiles_narrative),
        mo.ui.table(profile_table.select(["track_genre", "danceability_q10", "danceability_q50", "danceability_q90", "energy_q50", "valence_q50", "PC1", "PC2"])),
    ])
    return coordinates, pca, profiles


@app.cell
def _(EvidenceStatus, NarrativeSection, coordinates, go, mo, profiles, render_narrative_section):
    plot = coordinates.head(60)
    fig = go.Figure(go.Scattergl(x=plot["PC1"].to_numpy(), y=plot["PC2"].to_numpy(), mode="markers+text", text=plot["track_genre"].to_list(), textposition="top center", marker={"size": 8, "color": profiles.head(60)["danceability_q50"].to_numpy(), "colorscale": "Viridis", "colorbar": {"title": "danceability mediana"}}))
    fig.update_layout(title="PCA de perfis de gênero — 60 gêneros bounded", height=560, template="plotly_white")
    visual_narrative = NarrativeSection(
        title="Leitura da projeção de perfis",
        question="Quais gêneros têm perfis de áudio agregados semelhantes?",
        population="Os 60 gêneros com coordenadas exibidos no gráfico.",
        unit="um ponto por gênero; a cor representa danceability mediana",
        method="PCA reduz as 50 medidas de quantis a dois eixos para inspeção visual.",
        how_to_read="A posição combina os perfis; a cor é uma terceira medida independente.",
        denominator="Top 60 gêneros por ordem da tabela de coordenadas; não é seleção inferencial.",
        result="O gráfico torna comparáveis as vizinhanças de perfis em uma superfície 2D bounded.",
        interpretation="A figura formula hipóteses de similaridade, mas não prova grupos naturais.",
        use="Será comparada secundariamente com coocorrência e sensibilidades de população.",
        limitation="Não há teste de estabilidade ou validação de transferência nesta visualização.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"PCA": "projeção que resume variação em poucos eixos", "perfil": "resumo agregado de uma população de faixas"},
    )
    mo.vstack([render_narrative_section(mo, visual_narrative), fig])
    return (fig,)


@app.cell
def _(EvidenceStatus, NarrativeSection, artists, db, mo, pl, render_narrative_section, tracks):
    leaves = db.execute("""
        WITH genre_counts AS (SELECT track_id, COUNT(DISTINCT track_genre) AS k_genre FROM track_genres GROUP BY 1),
        artist_counts AS (SELECT track_id, COUNT(DISTINCT artist) AS k_artist FROM track_artists GROUP BY 1),
        top_genres AS (SELECT track_genre FROM track_genres GROUP BY 1 ORDER BY COUNT(DISTINCT track_id) DESC LIMIT 3),
        ranked_artists AS (
          SELECT tg.track_genre, ta.artist, SUM(1.0/(gc.k_genre*ac.k_artist)) AS area,
                 ROW_NUMBER() OVER (PARTITION BY tg.track_genre ORDER BY SUM(1.0/(gc.k_genre*ac.k_artist)) DESC, ta.artist) AS artist_rank
          FROM track_genres tg JOIN top_genres top USING(track_genre) JOIN track_artists ta USING(track_id)
          JOIN genre_counts gc USING(track_id) JOIN artist_counts ac USING(track_id)
          GROUP BY 1,2
        ),
        ranked_tracks AS (
          SELECT tg.track_genre, ta.artist, t.track_id, t.track_name, t.popularity,
                 SUM(1.0/(gc.k_genre*ac.k_artist)) AS area,
                 ROW_NUMBER() OVER (PARTITION BY tg.track_genre,ta.artist ORDER BY t.popularity DESC,t.track_id) AS track_rank
          FROM track_genres tg JOIN ranked_artists ra USING(track_genre) JOIN track_artists ta USING(track_id)
          JOIN tracks t USING(track_id) JOIN genre_counts gc USING(track_id) JOIN artist_counts ac USING(track_id)
          WHERE ra.artist_rank <= 5 AND ta.artist=ra.artist
          GROUP BY 1,2,3,4,5
        )
        SELECT * FROM ranked_tracks WHERE track_rank <= 5 ORDER BY track_genre, artist, popularity DESC
    """).pl()
    treemap_narrative = NarrativeSection(
        title="Treemap de relações do catálogo",
        question="Como a contribuição das faixas se distribui dentro dos gêneros e artistas mais representados?",
        population="Os três gêneros com mais faixas, cinco artistas por gênero e cinco faixas por artista.",
        unit="uma folha representa uma relação gênero–artista–faixa, com área fracionada",
        method="A área é dividida por número de gêneros e artistas associados à faixa; a cor da folha é popularity observada.",
        how_to_read="Ramos maiores acumulam mais contribuição fracionada; cor mais intensa indica maior popularity, não maior área.",
        denominator=f"{leaves.height} folhas após o limite explícito de 3×5×5; a tabela mostra 15.",
        result="A hierarquia conecta três entidades reais e mantém a visualização bounded.",
        interpretation="O treemap descreve composição do catálogo selecionado, sem afirmar que artista causa popularidade.",
        use="Serve como visão contextual e ponto de partida para auditoria de relações artista–gênero.",
        limitation="A regra de parsing de artistas e a interpretação de contribuição ainda precisam de auditoria dedicada.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"área fracionada": "contribuição dividida entre as relações da mesma faixa", "folha": "item final da hierarquia, aqui uma faixa"},
    )
    mo.vstack([
        mo.md("## 3. Treemap provisório: gênero → artista → faixa"),
        render_narrative_section(mo, treemap_narrative),
        mo.ui.table(leaves.head(15)),
    ])
    return (leaves,)


if __name__ == "__main__":
    app.run()
