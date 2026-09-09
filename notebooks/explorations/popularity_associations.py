# /// script
# requires-python = ">=3.12"
# dependencies = ["duckdb>=1.1,<2", "marimo>=0.14,<1", "numpy>=2,<3", "plotly>=5.24,<7", "polars>=1.20,<2", "scikit-learn>=1.5,<2", "statsmodels>=0.14,<1"]
# ///

"""Deterministic artist-level association analysis for observed popularity."""

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from hashlib import sha256
    from pathlib import Path
    from urllib.request import urlretrieve
    from zipfile import ZipFile
    root = Path.cwd()
    bundle_path = root / "spotify_molab_bundle.zip"
    if not (root / "spotify_data").exists() and bundle_path.exists():
        with ZipFile(bundle_path) as bundle: bundle.extractall(root)
    if not (root / "spotify_data").exists():
        # Pin the dependency bundle to a published commit containing the
        # helpers used by this notebook; Molab imports remain reproducible.
        snapshot = "cf7368ac8363aebe958eef56afb1de6f95abfc78"
        snapshot_root = root / f"desafio-01-{snapshot}"
        if not snapshot_root.exists():
            archive_path = root / f"desafio-01-{snapshot}.zip"
            urlretrieve(f"https://github.com/d4vidz/desafio-01/archive/{snapshot}.zip", archive_path)
            with ZipFile(archive_path) as archive: archive.extractall(root)
        root = snapshot_root
    if not (root / "spotify_data").exists(): root = Path(__file__).resolve().parents[2]
    csv_snapshot = root / "data" / "raw" / "spotify_tracks.csv"
    expected_source = "1a769bbbbb2fa4451d4309248349799ce8ab5efc21e053e2bb3aa28ddcb53d83"
    if csv_snapshot.exists():
        observed_source = sha256(csv_snapshot.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if observed_source != expected_source: raise RuntimeError("O snapshot Molab não corresponde ao hash canônico do CSV.")
    if str(root) not in sys.path: sys.path.insert(0, str(root))
    import marimo as mo
    import numpy as np
    import polars as pl
    import plotly.graph_objects as go
    from sklearn.impute import KNNImputer, SimpleImputer
    from spotify_data import EvidenceStatus, NarrativeSection, add_semantic_features, artist_partition, bh_fdr, build_data_layer, coefficient_confidence_intervals, eligible_group_summary, fit_clustered_ols, holm_adjust, joint_wald_test, random_effects_pool, render_narrative_section, synthetic_imputation_metrics
    return EvidenceStatus, KNNImputer, NarrativeSection, Path, SimpleImputer, add_semantic_features, artist_partition, bh_fdr, build_data_layer, coefficient_confidence_intervals, eligible_group_summary, fit_clustered_ols, go, holm_adjust, joint_wald_test, mo, np, pl, random_effects_pool, render_narrative_section, root, sha256, synthetic_imputation_metrics


@app.cell
def _(build_data_layer, mo, root):
    csv_path = root / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    track_genres = db.execute("SELECT track_id, track_genre FROM track_genres ORDER BY track_id, track_genre").pl()
    single = db.execute("SELECT t.*, MIN(ta.artist) AS primary_artist FROM tracks t JOIN track_artists ta USING(track_id) GROUP BY ALL HAVING COUNT(DISTINCT ta.artist) = 1 ORDER BY track_id").pl()
    return db, layer, single, track_genres, tracks


@app.cell
def _(EvidenceStatus, NarrativeSection, go, mo, render_narrative_section, tracks):
    fig = go.Figure(go.Histogram(x=tracks["popularity"].to_numpy(), nbinsx=40))
    fig.update_layout(title="Distribuição da popularity canônica", xaxis_title="popularity observada", yaxis_title="faixas", height=350, template="plotly_white")
    zeros = int((tracks["popularity"] == 0).sum())
    mo.vstack([mo.md("# Popularity: associações por artista"), fig, render_narrative_section(mo, NarrativeSection(title="Snapshot e grain", question="Como interpretar o outcome desta análise?", population="Tracks canônicas da camada compartilhada, com uma linha por track_id; a regressão usa apenas tracks de artista único.", unit="Uma faixa canônica; popularity é o score observado no snapshot.", method="A distribuição contextualiza amplitude, concentração e zeros antes das associações.", how_to_read="O eixo x é o score observado de 0 a 100; o eixo y é o número de faixas.", denominator=f"{tracks.height:,} tracks canônicas, {zeros:,} com popularity igual a zero e {tracks.filter(tracks['popularity_conflict']).height:,} conflitos.", result=f"Mediana `{tracks['popularity'].median():.1f}`; o score é observado e não representa sucesso futuro.", interpretation="O snapshot sustenta comparações e associações condicionais, não causalidade nem forecasting temporal.", use="Fixar a população e o teto de claims das seções seguintes.", limitation="A fonte é um catálogo observacional, com seleção, dependência por artista e possível heterogeneidade de gênero.", status=EvidenceStatus.PROTOTYPE, terms={"Grain": "Uma linha canônica por track_id.", "Popularity": "Score observado no catálogo, entre 0 e 100."}))])
    return (fig,)


@app.cell
def _(EvidenceStatus, NarrativeSection, add_semantic_features, artist_partition, coefficient_confidence_intervals, fit_clustered_ols, holm_adjust, joint_wald_test, mo, pl, render_narrative_section, single):
    human = ["danceability", "energy", "valence", "acousticness", "instrumentalness", "speechiness"]
    controls = ["explicit", "key_sin", "key_cos", "mode", "time_signature", "log_duration_ms"]
    frame = add_semantic_features(single).drop_nulls([*human, *controls, "popularity", "primary_artist"])
    split = artist_partition(frame["primary_artist"].to_list())
    discovery = frame.filter(pl.Series("stage", split == 0)); confirmation = frame.filter(pl.Series("stage", split == 1))
    discovery_model, _ = fit_clustered_ols(discovery, outcome="popularity", features=human, controls=controls, group="primary_artist")
    model, _ = fit_clustered_ols(confirmation, outcome="popularity", features=human, controls=controls, group="primary_artist")
    intervals = coefficient_confidence_intervals(model, list(range(1, len(human) + 1)))
    rows = [{"feature": feature, "effect_per_sd": float(model.params[i + 1]), "se_cluster": float(model.bse[i + 1]), "ci95_low": float(intervals[i, 0]), "ci95_high": float(intervals[i, 1]), "p_value": float(model.pvalues[i + 1]), "discovery_p": float(discovery_model.pvalues[i + 1])} for i, feature in enumerate(human)]
    association = pl.DataFrame(rows).with_columns(pl.Series("p_holm", holm_adjust([r["p_value"] for r in rows]))).with_columns((pl.col("p_holm") < 0.05).alias("holm_significant_0_05"), (pl.col("effect_per_sd").abs() >= 1.0).alias("practical_ge_1_point"))
    joint_p = joint_wald_test(model, len(human))
    omnibus = pl.DataFrame([{"n_tracks": confirmation.height, "n_artists": confirmation["primary_artist"].n_unique(), "r_squared": float(model.rsquared), "joint_wald_p": joint_p, "practical_threshold": "|effect_per_sd| >= 1 popularity point"}])
    mo.vstack([mo.md("## 1. Discovery → confirmation: painel humano"), mo.md("A divisão é por hash SHA-256 do artista; nenhuma faixa do mesmo artista atravessa as etapas. As seis features foram congeladas antes da confirmação."), mo.ui.table(association.with_columns(pl.col(["effect_per_sd", "se_cluster", "ci95_low", "ci95_high", "p_value", "p_holm", "discovery_p"]).round(4))), mo.ui.table(omnibus), render_narrative_section(mo, NarrativeSection(title="Confirmação com OLS agrupado", question="Quais associações condicionais das seis features centrais aparecem em artistas reservados?", population=f"{confirmation.height:,} tracks de {confirmation['primary_artist'].n_unique():,} artistas na partição confirmation; discovery tem {discovery['primary_artist'].n_unique():,} artistas.", unit="Uma faixa de artista único; a covariância é agrupada por primary_artist.", method="OLS padroniza as seis features, ajusta controles semânticos e usa erros-padrão clusterizados por artista. O teste conjunto de Wald é reportado separadamente dos CIs individuais; os seis p-valores individuais recebem Holm.", how_to_read="effect_per_sd é a associação em pontos de popularity por 1 SD; ci95_low/high é o intervalo individual de 95%; p_holm controla a família confirmatória; practical_ge_1_point marca o limiar de 1 ponto.", denominator=f"Amostra confirmation: {confirmation.height:,} faixas e {confirmation['primary_artist'].n_unique():,} clusters; discovery é diagnóstico.", result=f"R² `{model.rsquared:.3f}`; teste conjunto p=`{joint_p:.4g}`; `{int(association['practical_ge_1_point'].sum())}` de seis efeitos atingem ±1 ponto.", interpretation="São efeitos condicionais associativos no snapshot. Holm e o teste conjunto informam incerteza, não causalidade.", use="Tratar achados como hipóteses para replicação e generalização por artista não visto.", limitation="A divisão reduz leakage, mas não substitui validação temporal; a escolha de features e o limiar de 1 ponto são convenções de protótipo.", status=EvidenceStatus.PROTOTYPE, terms={"Cluster": "Grupo de faixas do mesmo artista.", "Holm": "Ajuste step-down dos seis testes individuais.", "Teste conjunto": "Wald para a hipótese de que todos os seis coeficientes são zero."}))])
    return association, confirmation, discovery, frame, human, model


@app.cell
def _(EvidenceStatus, NarrativeSection, bh_fdr, fit_clustered_ols, frame, human, mo, pl, render_narrative_section):
    screen_features = human + ["loudness", "liveness", "tempo", "duration_ms"]
    screen_rows = []
    for feature in screen_features:
        _screen_subset = frame.drop_nulls([feature, "popularity", "primary_artist"])
        _screen_fit, _ = fit_clustered_ols(_screen_subset, outcome="popularity", features=[feature], controls=[], group="primary_artist")
        screen_rows.append({"feature": feature, "effect_per_sd": float(_screen_fit.params[1]), "p_value": float(_screen_fit.pvalues[1]), "n": _screen_subset.height})
    screening = pl.DataFrame(screen_rows).with_columns(pl.Series("p_bh", bh_fdr([r["p_value"] for r in screen_rows]))).with_columns((pl.col("p_bh") < 0.05).alias("bh_fdr_05"))
    mo.vstack([mo.md("## 2. Screening exploratório BH-FDR"), mo.ui.table(screening.with_columns(pl.col(["effect_per_sd", "p_value", "p_bh"]).round(4))), render_narrative_section(mo, NarrativeSection(title="Screening de dez variáveis", question="Que variáveis são candidatas a investigação posterior?", population="Frame analítico de artista único; uma regressão clusterizada por feature.", unit="Uma faixa por observação, com clusters de artista.", method="Cada feature é padronizada e testada isoladamente; os dez p-valores recebem BH-FDR.", how_to_read="p_bh < 0,05 sinaliza descoberta exploratória; effect_per_sd mede pontos por 1 SD.", denominator="Cada linha informa n após o drop de nulos da própria feature.", result=f"{int(screening['bh_fdr_05'].sum())} de {len(screen_features)} variáveis passam BH-FDR 0,05 nesta execução.", interpretation="O screening prioriza hipóteses e não promove features a confirmação.", use="Escolher especificações futuras com controle explícito de multiplicidade.", limitation="Não é o modelo conjunto principal e não prova replicação, importância prática ou causalidade.", status=EvidenceStatus.PROTOTYPE, terms={"BH-FDR": "Ajuste que controla a proporção esperada de falsos achados entre descobertas."}))])
    return (screening,)


@app.cell
def _(EvidenceStatus, NarrativeSection, coefficient_confidence_intervals, confirmation, eligible_group_summary, fit_clustered_ols, human, mo, pl, random_effects_pool, render_narrative_section, track_genres):
    # The confirmatory population is deliberately narrower than the catalogue:
    # confirmation artists and tracks with exactly one genre membership.
    with_genre = confirmation.filter(pl.col("genre_count") == 1).join(track_genres, on="track_id", how="inner")
    eligible_genres = eligible_group_summary(with_genre, group="track_genre", cluster="primary_artist", min_tracks=300, min_clusters=100)
    genres = eligible_genres["track_genre"].to_list()
    cross_genre_artists = with_genre.filter(pl.col("track_genre").is_in(genres)).group_by("primary_artist").agg(pl.col("track_genre").n_unique().alias("n_genres")).filter(pl.col("n_genres") > 1).height
    genre_rows = []
    genre_controls = ["explicit", "key_sin", "key_cos", "mode", "time_signature", "log_duration_ms"]
    for genre in genres:
        _genre_subset = with_genre.filter(pl.col("track_genre") == genre)
        _genre_fit, _ = fit_clustered_ols(_genre_subset, outcome="popularity", features=human, controls=genre_controls, group="primary_artist")
        _intervals = coefficient_confidence_intervals(_genre_fit, list(range(1, len(human) + 1)))
        genre_rows.extend({"track_genre": genre, "feature": feature, "estimate": float(_genre_fit.params[i + 1]), "standard_error": float(_genre_fit.bse[i + 1]), "ci95_low": float(_intervals[i, 0]), "ci95_high": float(_intervals[i, 1]), "n_tracks": _genre_subset.height, "n_artists": _genre_subset["primary_artist"].n_unique()} for i, feature in enumerate(human))
    genre_estimates = pl.DataFrame(genre_rows) if genre_rows else pl.DataFrame(schema={"track_genre": pl.String, "feature": pl.String, "estimate": pl.Float64, "standard_error": pl.Float64, "ci95_low": pl.Float64, "ci95_high": pl.Float64, "n_tracks": pl.UInt32, "n_artists": pl.UInt32})
    pooled = pl.DataFrame([{"feature": feature, **random_effects_pool(genre_estimates.filter(pl.col("feature") == feature).select(["estimate", "standard_error"]))} for feature in human])
    pooled_effects = pooled.select(["feature", "estimate", "standard_error", "ci_low", "ci_high"])
    pool_diagnostics = pooled.select(["feature", "q", "q_df", "i2", "tau2", "n"])
    mo.vstack([mo.md("## 3. Heterogeneidade por gênero e pooling"), mo.md("A população confirmatória usa somente artistas da partição confirmation e tracks com `genre_count = 1`. Todos os gêneros que passam os dois cortes são estimados; a tabela pode ser filtrada visualmente depois sem alterar as estimativas."), mo.ui.table(eligible_genres), mo.ui.table(genre_estimates.with_columns(pl.col(["estimate", "standard_error", "ci95_low", "ci95_high"]).round(4))), mo.md("### Efeitos pooled (CI individual do resumo)"), mo.ui.table(pooled_effects.with_columns(pl.col(["estimate", "standard_error", "ci_low", "ci_high"]).round(4))), mo.md("### Diagnósticos de heterogeneidade (separados do CI)"), mo.ui.table(pool_diagnostics.with_columns(pl.col(["q", "q_df", "i2", "tau2"]).round(4))), render_narrative_section(mo, NarrativeSection(title="Heterogeneidade e resumo pooled", question="Os efeitos do painel humano variam entre gêneros?", population=f"{with_genre.height:,} tracks de artista único na partição confirmation e com gênero único; {eligible_genres.height} gêneros são elegíveis.", unit="Uma faixa de gênero único; clusters continuam sendo artistas.", method="Cada gênero elegível recebe o mesmo OLS clusterizado. CIs de 95% acompanham coeficientes individuais; o pooling DerSimonian–Laird resume os efeitos e seus CIs, enquanto Q, I² e tau² aparecem em diagnósticos separados.", how_to_read="estimate e ci_low/high descrevem o resumo pooled; ci95_low/high na tabela de gêneros são intervalos por gênero; Q e I² medem heterogeneidade e não substituem intervalos.", denominator=f"{genre_estimates['track_genre'].n_unique()} gêneros elegíveis e {genre_estimates.height} coeficientes estimados; cortes aplicados antes de qualquer apresentação.", result=f"Foram estimados {genre_estimates['track_genre'].n_unique()} gêneros elegíveis e resumidos {pooled.height} efeitos pooled.", interpretation="Um efeito médio pode esconder reversões entre gêneros; leia estimativa, intervalo e I² em conjunto.", use="Orientar replicações estratificadas e decisões sobre pooling futuro.", limitation="O recorte por gênero único reduz cobertura e não sustenta generalização causal; a análise continua exploratória.", status=EvidenceStatus.PROTOTYPE, terms={"I²": "Fração descritiva da variabilidade entre estimativas.", "Q": "Estatística de heterogeneidade antes da interpretação do pooling."}))])
    return cross_genre_artists, genre_estimates, pooled


@app.cell
def _(cross_genre_artists, mo):
    mo.callout(
        f"O pooling trata estimativas por gênero como independentes; "
        f"{cross_genre_artists} artista(s) aparece(m) em mais de um gênero elegível. "
        "Essa dependência residual limita a interpretação do resumo.",
        kind="warn",
    )
    return


@app.cell
def _(EvidenceStatus, KNNImputer, NarrativeSection, SimpleImputer, confirmation, fit_clustered_ols, human, mo, np, pl, render_narrative_section, synthetic_imputation_metrics, tracks):
    conflict_ids = tracks.filter(pl.col("popularity_conflict"))["track_id"]
    conflict_free = confirmation.filter(~pl.col("track_id").is_in(conflict_ids.to_list()))
    sensitivity_rows = []
    model_controls = ["explicit", "key_sin", "key_cos", "mode", "time_signature", "log_duration_ms"]
    for label, _scenario_subset, target in [("primary", confirmation, "popularity"), ("sem_conflitos", conflict_free, "popularity")]:
        _scenario_fit, _ = fit_clustered_ols(_scenario_subset, outcome=target, features=human, controls=model_controls, group="primary_artist")
        sensitivity_rows.append({"scenario": label, "n_tracks": _scenario_subset.height, "r_squared": float(_scenario_fit.rsquared), **{f"{feature}_effect": float(_scenario_fit.params[i + 1]) for i, feature in enumerate(human)}})
    clipped = confirmation.with_columns(pl.col("popularity").clip(confirmation["popularity"].quantile(0.01), confirmation["popularity"].quantile(0.99)).alias("popularity_clipped"))
    fit_clip, _ = fit_clustered_ols(clipped, outcome="popularity_clipped", features=human, controls=model_controls, group="primary_artist")
    sensitivity_rows.append({"scenario": "target_winsor_1_99", "n_tracks": clipped.height, "r_squared": float(fit_clip.rsquared), **{f"{feature}_effect": float(fit_clip.params[i + 1]) for i, feature in enumerate(human)}})
    sensitivities = pl.DataFrame(sensitivity_rows)
    imputation_seed = 2026; rng = np.random.default_rng(imputation_seed); observed = confirmation.select(human).to_numpy().astype(float); mask = rng.random(observed.shape) < 0.15; synthetic = observed.copy(); synthetic[mask] = np.nan
    train_rows = np.arange(observed.shape[0]) < max(1, int(observed.shape[0] * 0.8))
    imputation_rows = []
    for name, transformer in [("complete_case", None), ("median", SimpleImputer(strategy="median")), ("knn_k5", KNNImputer(n_neighbors=5))]:
        metrics = synthetic_imputation_metrics(observed, synthetic, mask, transformer=transformer, train_rows=train_rows)
        imputation_rows.append({"method": name, "synthetic_missing_fraction": float(mask.mean()), **metrics})
    imputation = pl.DataFrame(imputation_rows)
    mo.vstack([mo.md("## 4. Sensibilidades e missingness sintética"), mo.ui.table(sensitivities.with_columns(pl.col(sensitivities.columns[2:]).round(4))), mo.ui.table(imputation), render_narrative_section(mo, NarrativeSection(title="Robustez, conflitos, extremos e missingness", question="O padrão muda sob decisões de robustez e sob missingness controlada?", population="Confirmation, repetida sem conflitos e com popularity winsorizada; o apêndice mascara somente uma cópia sintética das seis features.", unit="Uma faixa por linha; clusters de artista no OLS.", method="Comparamos o mesmo modelo em três cenários. Depois mascaramos 15% das features com seed 2026; complete-case informa somente retenção, enquanto mediana e KNN ajustam no subconjunto de treino e avaliam `masked_mae` apenas nas células mascaradas. Nenhum valor real é imputado e não há MAE preditivo de popularity nesta célula.", how_to_read="Compare sinais e magnitudes entre cenários. Na simulação, `retention_fraction` é a retenção complete-case e `masked_mae` é o erro de reconstrução somente nas células mascaradas.", denominator=f"{confirmation.height:,} tracks na referência; {confirmation.height - conflict_free.height:,} sem conflitos; a máscara cobre {int(mask.sum()):,} células.", result=f"Foram calculados {sensitivities.height} cenários de robustez e {imputation.height} estratégias sintéticas.", interpretation="Semelhança entre cenários apoia a descrição no snapshot; divergência é informação de risco.", use="Registrar riscos de conflitos, extremos e dados faltantes antes de claims mais fortes.", limitation="A simulação não informa o mecanismo real de missingness; seu erro não mede previsão de popularity e associação não vira causalidade.", status=EvidenceStatus.PROTOTYPE, terms={"Winsorizar": "Limitar extremos aos percentis declarados em uma repetição.", "Missingness sintética": "Máscara reproduzível em cópia, sem alterar dados reais.", "masked_mae": "Erro absoluto médio somente nas células artificialmente mascaradas."}))])
    return imputation, sensitivities


@app.cell
def _(mo):
    mo.callout(
        "Na simulação, train_masked_mae é apenas diagnóstico no treino; "
        "masked_mae é calculado somente nas células mascaradas do holdout. "
        "Nenhuma das duas métricas avalia previsão de popularity.",
        kind="info",
    )
    return


if __name__ == "__main__":
    app.run()
