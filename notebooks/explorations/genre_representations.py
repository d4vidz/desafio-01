"""Representações de gênero: multi-hot, PPMI/SVD e perfis de áudio."""

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
    from spotify_data import (CONTINUOUS_AUDIO_FEATURES, build_data_layer,
                              fit_genre_ppmi, genre_audio_profiles,
                              genre_membership_matrix, robust_pca_profiles)
    return CONTINUOUS_AUDIO_FEATURES, Path, build_data_layer, fit_genre_ppmi, genre_audio_profiles, genre_membership_matrix, go, mo, np, pl, robust_pca_profiles


@app.cell
def _(Path, build_data_layer, mo):
    csv_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    genres = db.execute("SELECT * FROM track_genres ORDER BY track_id, track_genre").pl()
    artists = db.execute("SELECT * FROM track_artists ORDER BY track_id, artist_position").pl()
    return artists, db, genres, layer, tracks


@app.cell
def _(genres, mo, pl, tracks):
    support = genres.group_by("track_genre").agg(pl.col("track_id").n_unique().alias("faixas"), pl.col("track_id").n_unique().alias("memberships"))
    support = support.with_columns((pl.col("faixas") < 300).alias("aviso_esparsidade")).sort("faixas", descending=True)
    multi = tracks.filter(pl.col("genre_count") > 1).height
    mo.vstack([
        mo.md("# Representações de gênero e relações conectadas"),
        mo.ui.table(support.head(20)),
        mo.md(f"Há `{support.height}` gêneros; `{multi:,}` faixas canônicas são multigênero. O relatório inferencial standalone exige 300 faixas e 100 artistas de gênero único; populações multigênero são mantidas para representação e sensibilidade."),
    ])
    return (support,)


@app.cell
def _(fit_genre_ppmi, genre_membership_matrix, genres, mo, np, pl, tracks):
    ids = tracks["track_id"].to_list()
    multi_hot, vocabulary = genre_membership_matrix(genres, ids)
    embedding = fit_genre_ppmi(genres, ids, n_components=8)
    embeddings = embedding.transform(genres, ids).filter(pl.col("track_id").is_in(ids[:3000]))
    overview = pl.DataFrame({
        "representacao": ["sem gênero", "multi-hot", "PPMI + TruncatedSVD"],
        "dimensoes": [0, len(vocabulary), 8],
        "ajuste": ["baseline", "vocabulário do treino", "coocorrência; fold-local em predição"],
    })
    mo.vstack([
        mo.md("## 1. Ladder obrigatório"),
        mo.ui.table(overview),
        mo.ui.table(embeddings.head(8).with_columns(pl.all().exclude("track_id").round(3))),
        mo.md(f"O embedding primário usa `{embedding.n_components}D`; 4D/16D são sensibilidades. OOV recebe vetor zero e faixas multigênero recebem a média dos vetores de seus gêneros. O ajuste desta célula usa o snapshot inteiro apenas para EDA; modelos devem ajustar o embedding dentro de cada fold."),
    ])
    return embedding, embeddings, multi_hot, overview, vocabulary


@app.cell
def _(genre_audio_profiles, genres, mo, pl, robust_pca_profiles, tracks):
    profiles = genre_audio_profiles(tracks, genres)
    coordinates, pca = robust_pca_profiles(profiles)
    profile_table = profiles.join(coordinates, on="track_genre").head(20)
    mo.vstack([
        mo.md("## 2. Perfil de áudio por gênero"),
        mo.ui.table(profile_table.select(["track_genre", "danceability_q10", "danceability_q50", "danceability_q90", "energy_q50", "valence_q50", "PC1", "PC2"])),
        mo.md(f"Perfil primário: todas as memberships, 50 dimensões (10 features × 5 quantis), RobustScaler e PCA. Sensibilidades: gênero único e peso fracionário 1/k; a proximidade do perfil não equivale a coocorrência."),
    ])
    return coordinates, pca, profiles


@app.cell
def _(coordinates, go, mo, profiles):
    plot = coordinates.head(60)
    fig = go.Figure(go.Scattergl(x=plot["PC1"].to_numpy(), y=plot["PC2"].to_numpy(), mode="markers+text", text=plot["track_genre"].to_list(), textposition="top center", marker={"size": 8, "color": profiles.head(60)["danceability_q50"].to_numpy(), "colorscale": "Viridis", "colorbar": {"title": "danceability mediana"}}))
    fig.update_layout(title="PCA de perfis de gênero — 60 gêneros bounded", height=560, template="plotly_white")
    mo.vstack([fig, mo.md("A visão resume áudio por gênero, não prova fronteiras naturais. Compare suas vizinhanças com a matriz de coocorrência antes de falar em transferência de conhecimento." )])
    return (fig,)


@app.cell
def _(artists, db, mo, pl, tracks):
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
    mo.vstack([
        mo.md("## 3. Treemap provisório: gênero → artista → faixa"),
        mo.ui.table(leaves.head(15)),
        mo.md("Hierarquia conectada e bounded: 3 gêneros × 5 artistas × 5 faixas. Área é contribuição fracionária aditiva `1/(n gêneros × n artistas)`; cor da folha é popularity observada. A mesma faixa pode aparecer em mais de um ramo por sua relação real com gêneros/artistas."),
    ])
    return (leaves,)


if __name__ == "__main__":
    app.run()
