"""PCA, loadings and stability-gated clustering of the audio space."""

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
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import RobustScaler, StandardScaler
    from spotify_data import (CONTINUOUS_AUDIO_FEATURES, EvidenceStatus,
                              NarrativeSection, build_data_layer,
                              clustering_stability, render_narrative_section)
    return CONTINUOUS_AUDIO_FEATURES, EvidenceStatus, NarrativeSection, PCA, Path, RobustScaler, StandardScaler, build_data_layer, clustering_stability, go, mo, np, pl, render_narrative_section, root


@app.cell
def _(Path, build_data_layer, mo, root):
    csv_path = root / "data" / "raw" / "spotify_tracks.csv"
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
def _(EvidenceStatus, NarrativeSection, go, loadings, mo, pca_frame, render_narrative_section, variance):
    plot = pca_frame.sample(n=min(4_000, pca_frame.height), seed=2026)
    fig = go.Figure(go.Scattergl(x=plot["PC1"].to_numpy(), y=plot["PC2"].to_numpy(), mode="markers", marker={"size": 5, "opacity": 0.45, "color": plot["PC3"].to_numpy(), "colorscale": "Viridis", "colorbar": {"title": "PC3"}}, text=plot["representative_track_genre"].to_list(), hovertemplate="gênero=%{text}<br>PC1=%{x:.2f}<br>PC2=%{y:.2f}<extra></extra>"))
    fig.update_layout(title="PCA 2D — cor por PC3; amostra bounded", height=520, template="plotly_white")
    pca_narrative = NarrativeSection(
        title="PCA e estrutura do espaço de áudio",
        question="Quais combinações de features explicam a maior parte da variação observada?",
        population=f"{pca_frame.height:,} faixas canônicas amostradas do catálogo.",
        unit="um ponto por faixa; cor indica PC3 e texto mostra o gênero representativo",
        method="Padronizamos dez features contínuas e projetamos combinações em componentes principais; loadings mostram a contribuição de cada feature.",
        how_to_read="PC1/PC2 são combinações, não colunas originais; a variância explicada informa quanto cada componente resume.",
        denominator=f"A amostra tem até 6.000 faixas e {len(loadings)} features na tabela de loadings.",
        result=f"Os três componentes exibidos explicam {variance['variancia_explicada'].sum():.1%} da variância padronizada.",
        interpretation="A projeção compacta permite inspecionar estrutura musical, sem provar dimensões psicológicas ou gêneros naturais.",
        use="Os componentes orientam a inspeção exploratória de clustering em #35.",
        limitation="RobustScaler, log-duration e estabilidade com referência/null permanecem sensibilidades não concluídas.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"loading": "peso de uma feature na combinação que forma um componente", "variância explicada": "fração da variação resumida por um componente"},
    )
    mo.vstack([mo.md("# Musical structure: PCA e clustering"), render_narrative_section(mo, pca_narrative), fig, mo.hstack([mo.ui.table(variance), mo.ui.table(loadings)], widths="equal")])
    return (fig,)


@app.cell
def _(EvidenceStatus, NarrativeSection, clustering_stability, mo, render_narrative_section, standard):
    stability = clustering_stability(standard, k_values=range(2, 9), repeats=2, sample_size=3_000)
    robust_candidates = stability.filter(stability["gate_ari"])
    claim = "há candidatos estáveis para inspeção" if robust_candidates.height else "não há clusters naturais robustos pelo gate ARI ≥ 0,70"
    stability_narrative = NarrativeSection(
        title="Estabilidade e gate de clustering",
        question="Os agrupamentos reaparecem quando reamostramos as faixas?",
        population="A matriz padronizada, avaliada com K-means e Gaussian Mixtures para k=2..8.",
        unit="uma linha por algoritmo e número de clusters",
        method="Repetimos ajustes em amostras e comparamos atribuições por ARI; o gate mínimo atual é ARI mediana ≥ 0,70.",
        how_to_read="ARI alto indica concordância entre repetições; silhouette mede separação interna. Nenhuma isoladamente prova segmentação substantiva.",
        denominator=f"{stability.height} combinações foram calculadas com duas repetições exploratórias.",
        result=f"Nesta execução, {claim}.",
        interpretation="Este é um diagnóstico inicial de repetibilidade, não uma conclusão sobre clusters naturais.",
        use="A seleção final depende do protocolo de #35, incluindo referência/null e sensibilidades.",
        limitation="Referência/null, repetição completa e avaliação de sensibilidade ainda não foram executadas.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"ARI": "concordância entre partições ajustada ao acaso", "stability": "persistência do agrupamento sob reamostragem"},
    )
    mo.vstack([mo.md("## Estabilidade e gate de clusters"), render_narrative_section(mo, stability_narrative), mo.ui.table(stability)])
    return (stability,)


@app.cell
def _(EvidenceStatus, NarrativeSection, mo, pca_frame, render_narrative_section, stability):
    best = stability.sort(["gate_ari", "ARI_mediana", "silhouette"], descending=True).head(1)
    brief = NarrativeSection(
        title="Evidence brief da estrutura musical",
        question="O que já podemos afirmar com segurança sobre esta exploração?",
        population="A mesma amostra bounded do notebook.",
        unit="resumo do melhor candidato segundo o gate exploratório",
        method="Consolidamos o candidato mais estável entre os resultados calculados, sem transformar o ranking em validação.",
        how_to_read="A tabela é um índice de auditoria; consulte PCA, loadings e estabilidade antes de interpretar candidatos.",
        denominator=f"A nuvem 2D é limitada a {min(4_000, pca_frame.height):,} pontos.",
        result="O notebook oferece uma projeção e um diagnóstico bounded, mas não encerra a investigação de clusters.",
        interpretation="A conclusão permitida é descritiva: a estrutura pode ser inspecionada, sem afirmar personas ou fronteiras naturais.",
        use="O resultado orienta a especificação de estabilidade e null em #35.",
        limitation="Clustering completo, null e 3D permanecem follow-up; não há claim final neste notebook.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"evidence brief": "resumo curto que aponta resultado, evidência e limites para revisão"},
    )
    mo.vstack([mo.md("## Evidence brief"), render_narrative_section(mo, brief), mo.ui.table(best)])
    return


if __name__ == "__main__":
    app.run()
