import marimo


__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import duckdb
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    return KMeans, PCA, Path, StandardScaler, duckdb, go, mo, np, pl


@app.cell
def _(Path, mo):
    csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"Input CSV not found: `{csv_path}`"))
    return (csv_path,)


@app.cell
def _(csv_path, duckdb, pl):
    # The database is intentionally ephemeral: each Marimo runtime starts here.
    duckdb_conn = duckdb.connect(":memory:")
    duckdb_conn.execute(
        "CREATE TEMP TABLE tracks_raw AS SELECT * FROM read_csv_auto(?, sample_size=-1, nullstr='')",
        [str(csv_path)],
    )
    duckdb_conn.execute(
        """
        CREATE TEMP TABLE track_genres AS
        SELECT DISTINCT track_id, track_genre
        FROM tracks_raw
        WHERE track_id IS NOT NULL AND track_genre IS NOT NULL
        """
    )
    duckdb_conn.execute(
        """
        CREATE TEMP TABLE tracks AS
        SELECT
            track_id,
            any_value(artists) AS artists,
            any_value(album_name) AS album_name,
            any_value(track_name) AS track_name,
            any_value(track_genre) AS display_genre,
            median(popularity) AS popularity,
            any_value(duration_ms) AS duration_ms,
            any_value(explicit) AS explicit,
            any_value(danceability) AS danceability,
            any_value(energy) AS energy,
            any_value(loudness) AS loudness,
            any_value(speechiness) AS speechiness,
            any_value(acousticness) AS acousticness,
            any_value(instrumentalness) AS instrumentalness,
            any_value(liveness) AS liveness,
            any_value(valence) AS valence,
            any_value(tempo) AS tempo
        FROM tracks_raw
        WHERE track_id IS NOT NULL
        GROUP BY track_id
        """
    )
    tracks_raw = duckdb_conn.execute("SELECT * FROM tracks_raw").pl()
    tracks = duckdb_conn.execute("SELECT * FROM tracks").pl()
    track_genres = duckdb_conn.execute("SELECT * FROM track_genres").pl()
    genre_catalog = track_genres.join(tracks, on="track_id", how="inner")
    data_contract = pl.DataFrame(
        {
            "relation": ["tracks_raw", "tracks", "track_genres"],
            "rows": [tracks_raw.height, tracks.height, track_genres.height],
            "grain": ["source CSV row", "one row per track_id", "track_id x track_genre edge"],
        }
    )
    return data_contract, duckdb_conn, genre_catalog, track_genres, tracks, tracks_raw


@app.cell
def _(data_contract, mo):
    mo.vstack(
        [
            mo.md("# Spotify track analysis\n\nA reproducible, evidence-led first pass. DuckDB is rebuilt in memory from the committed CSV on every runtime start."),
            mo.md("## Runtime data contract"),
            mo.ui.table(data_contract),
        ]
    )
    return


@app.cell
def _(pl, tracks, tracks_raw):
    missingness = tracks_raw.select(
        [pl.col(column).is_null().sum().alias(column) for column in tracks_raw.columns]
    ).transpose(include_header=True, header_name="column", column_names=["missing"])
    repeated_track_ids = (
        tracks_raw.group_by("track_id")
        .len()
        .filter(pl.col("len") > 1)
        .height
    )
    duplicate_audit = pl.DataFrame(
        {
            "metric": ["raw rows", "unique track IDs", "repeated track IDs", "exact duplicate rows"],
            "value": [
                tracks_raw.height,
                tracks.height,
                repeated_track_ids,
                tracks_raw.is_duplicated().sum(),
            ],
        }
    )
    domain_checks = pl.DataFrame(
        {
            "check": ["zero duration", "zero tempo", "popularity outside 0-100"],
            "rows": [
                tracks_raw.filter(pl.col("duration_ms") <= 0).height,
                tracks_raw.filter(pl.col("tempo") <= 0).height,
                tracks_raw.filter((pl.col("popularity") < 0) | (pl.col("popularity") > 100)).height,
            ],
        }
    )
    return domain_checks, duplicate_audit, missingness


@app.cell
def _(domain_checks, duplicate_audit, missingness, mo):
    mo.vstack(
        [
            mo.md("## Data quality and source grain\n\nThe raw table is not automatically a track-level table; repeated `track_id` values are retained here and resolved explicitly downstream."),
            mo.ui.table(missingness.filter(missingness["missing"] > 0)),
            mo.ui.table(duplicate_audit),
            mo.ui.table(domain_checks),
        ]
    )
    return


@app.cell
def _(track_genres):
    genre_options = sorted(track_genres.get_column("track_genre").unique().to_list())
    return (genre_options,)


@app.cell
def _(genre_options, mo):
    genre_selector = mo.ui.dropdown(options=genre_options, value=genre_options[0], label="Genre")
    genre_selector
    return (genre_selector,)


@app.cell
def _(duckdb_conn, genre_selector, go):
    selected_genre = genre_selector.value
    genre_profile = duckdb_conn.execute(
        """
        SELECT count(*) AS track_genre_edges, count(DISTINCT track_id) AS unique_tracks,
               median(popularity) AS median_popularity, avg(energy) AS mean_energy,
               avg(danceability) AS mean_danceability, avg(acousticness) AS mean_acousticness
        FROM track_genres JOIN tracks USING (track_id)
        WHERE track_genre = ?
        """,
        [selected_genre],
    ).pl()
    genre_points = duckdb_conn.execute(
        """
        SELECT track_name, artists, popularity, energy, danceability
        FROM track_genres JOIN tracks USING (track_id)
        WHERE track_genre = ?
        LIMIT 2500
        """,
        [selected_genre],
    ).pl().drop_nulls()
    fig_genre = go.Figure(go.Scattergl(
        x=genre_points.get_column("energy").to_numpy(),
        y=genre_points.get_column("danceability").to_numpy(),
        mode="markers",
        marker={"size": 6, "opacity": 0.55, "color": genre_points.get_column("popularity").to_numpy(), "colorscale": "Viridis", "colorbar": {"title": "Popularity"}},
        text=(genre_points.get_column("track_name") + " - " + genre_points.get_column("artists")).to_list(),
        hovertemplate="%{text}<br>energy=%{x:.2f}<br>danceability=%{y:.2f}<extra></extra>",
    ))
    fig_genre.update_layout(title=f"{selected_genre}: energy and danceability", xaxis_title="Energy", yaxis_title="Danceability", template="plotly_white", height=460)
    return fig_genre, genre_profile, selected_genre


@app.cell
def _(fig_genre, genre_profile, genre_selector, mo):
    mo.vstack([
        mo.md("## Genre-specific profile"),
        genre_selector,
        mo.ui.table(genre_profile),
        fig_genre,
        mo.md("This section counts the selected track-genre relationships. The PCA section below uses one canonical row per track."),
    ])
    return


@app.cell
def _(go, tracks):
    feature_columns = ["danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo"]
    pca_source = tracks.select(["track_id", "popularity"] + feature_columns).drop_nulls()
    if pca_source.height > 20000:
        pca_source = pca_source.sample(n=20000, seed=2026)
    return feature_columns, pca_source


@app.cell
def _(KMeans, PCA, StandardScaler, feature_columns, np, pca_source, pl):
    scaled_features = StandardScaler().fit_transform(pca_source.select(feature_columns).to_numpy())
    pca_model = PCA(n_components=3, random_state=2026)
    pca_values = pca_model.fit_transform(scaled_features)
    cluster_model = KMeans(n_clusters=3, n_init=10, random_state=2026)
    clusters = cluster_model.fit_predict(scaled_features)
    pca_frame = pca_source.with_columns(
        [
            pl.Series("PC1", pca_values[:, 0]),
            pl.Series("PC2", pca_values[:, 1]),
            pl.Series("PC3", pca_values[:, 2]),
            pl.Series("cluster", clusters),
        ]
    )
    pca_variance = pl.DataFrame({"component": ["PC1", "PC2", "PC3"], "explained_variance": pca_model.explained_variance_ratio_}).with_columns(pl.col("explained_variance").round(4))
    return pca_frame, pca_variance


@app.cell
def _(go, pca_frame, pca_variance):
    fig_pca = go.Figure(go.Scattergl(
        x=pca_frame.get_column("PC1").to_numpy(),
        y=pca_frame.get_column("PC2").to_numpy(),
        mode="markers",
        marker={"size": 4, "opacity": 0.45, "color": pca_frame.get_column("cluster").to_numpy(), "colorscale": "Viridis"},
        hovertemplate="PC1=%{x:.2f}<br>PC2=%{y:.2f}<extra></extra>",
    ))
    fig_pca.update_layout(title="PCA projection of canonical tracks", xaxis_title="PC1", yaxis_title="PC2", template="plotly_white", height=540)
    return fig_pca


@app.cell
def _(fig_pca, mo, pca_variance):
    mo.vstack([
        mo.md("## PCA and exploratory clustering\n\nClusters summarize audio-feature geometry. They are not listener segments or a musical taxonomy."),
        mo.ui.table(pca_variance),
        fig_pca,
    ])
    return


@app.cell
def _(duckdb_conn, go, np):
    top_genres = duckdb_conn.execute("SELECT track_genre FROM track_genres GROUP BY 1 ORDER BY count(*) DESC LIMIT 14").fetchall()
    graph_genres = [row[0] for row in top_genres]
    overlap = duckdb_conn.execute(
        """
        SELECT a.track_genre AS genre_a, b.track_genre AS genre_b, count(DISTINCT a.track_id) AS shared_tracks
        FROM track_genres a JOIN track_genres b ON a.track_id = b.track_id AND a.track_genre < b.track_genre
        WHERE a.track_genre IN (SELECT unnest(?)) AND b.track_genre IN (SELECT unnest(?))
        GROUP BY 1, 2
        """,
        [graph_genres, graph_genres],
    ).fetchall()
    overlap_index = {genre: index for index, genre in enumerate(graph_genres)}
    overlap_matrix = np.zeros((len(graph_genres), len(graph_genres)), dtype=int)
    for genre_a, genre_b, shared in overlap:
        overlap_matrix[overlap_index[genre_a], overlap_index[genre_b]] = shared
        overlap_matrix[overlap_index[genre_b], overlap_index[genre_a]] = shared
    fig_overlap = go.Figure(go.Heatmap(z=overlap_matrix, x=graph_genres, y=graph_genres, colorscale="Blues", hovertemplate="%{y} and %{x}: %{z} shared tracks<extra></extra>"))
    fig_overlap.update_layout(title="Genre-overlap graph: shared track IDs", template="plotly_white", height=600)
    return fig_overlap


@app.cell
def _(fig_overlap, mo):
    mo.vstack([
        mo.md("## Derived graph view\n\nThis is an aggregated projection of track-genre edges, not a listener or influence network."),
        fig_overlap,
    ])
    return


@app.cell
def _(mo):
    interpretation_text = "\n".join(
        [
            "## Interpretation boundaries",
            "",
            "- Popularity is an observed catalogue field, not a causal outcome or a future-hit label.",
            "- Multi-genre tracks are intentionally counted in each associated genre view but only once in canonical-track PCA and clustering.",
            "- Any predictive extension must define a target, prevent leakage, and beat transparent baselines on held-out data.",
        ]
    )
    mo.md(interpretation_text)
    return


if __name__ == "__main__":
    app.run()
