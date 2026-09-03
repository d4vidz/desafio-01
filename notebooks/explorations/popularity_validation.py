"""Validation of observed popularity with unseen-artist splits."""

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
    import polars as pl
    from spotify_data import (
        EvidenceStatus,
        NarrativeSection,
        add_semantic_features,
        build_data_layer,
        render_narrative_section,
    )
    from spotify_data.evaluation import evaluate_regression, summarize_metrics
    return (EvidenceStatus, NarrativeSection, Path, add_semantic_features,
            build_data_layer, evaluate_regression, mo, pl,
            render_narrative_section, root, summarize_metrics)


@app.cell
def _(Path, build_data_layer, mo, root):
    csv_path = root / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    # Primary evaluation population: one artist per track. Collaborations are
    # reported separately in the final protocol instead of leaking across folds.
    model_frame = db.execute("""
        SELECT t.*, MIN(ta.artist) AS primary_artist
        FROM tracks t JOIN track_artists ta USING(track_id)
        GROUP BY ALL HAVING COUNT(DISTINCT ta.artist) = 1
        ORDER BY track_id
    """).pl()
    return layer, model_frame


@app.cell
def _(EvidenceStatus, NarrativeSection, add_semantic_features, evaluate_regression,
      model_frame, mo, pl, render_narrative_section, summarize_metrics):
    numeric = ["danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo", "log_duration_ms", "key_sin", "key_cos", "explicit_binary", "mode_binary"]
    prepared = add_semantic_features(model_frame)
    # A deterministic cap keeps the exploratory notebook responsive. The
    # final run can remove the cap without changing the split/model protocol.
    prepared = prepared.sample(n=min(40_000, prepared.height), seed=2026)
    results = evaluate_regression(prepared, numeric, repeats=5)
    summary = summarize_metrics(results)
    grouped = summary.filter(pl.col("split") == "artista não visto")
    best = grouped.sort("MAE_média").row(0, named=True)
    narrative = NarrativeSection(
        title="Validação preditiva da popularidade observada",
        question="As audio features generalizam para faixas de artistas que não aparecem no treino?",
        population=f"{prepared.height:,} faixas de artista único do snapshot".replace(",", "."),
        unit="uma faixa canônica",
        method="Comparamos uma baseline de mediana e modelos de regressão no split principal por artista não visto; o split aleatório serve apenas como diagnóstico otimista.",
        how_to_read="Compare o MAE entre modelos dentro do split principal: menor erro é melhor. A tabela também mostra RMSE e R² como métricas secundárias.",
        denominator=f"{grouped.height} combinações de modelo no resumo; cinco repetições 80/20 por artista.",
        result=f"O menor MAE médio observado no split por artista foi {best['MAE_média']:.2f}, para o modelo {best['modelo']}.",
        interpretation="Este é um diagnóstico de generalização contemporânea no snapshot, não uma previsão temporal de sucesso futuro.",
        use="Orientar a especificação dos experimentos preditivos e a escolha de ablações que serão validadas em uma entrega posterior.",
        limitation="Ainda faltam bootstrap pareado agrupado, estratos de colaboração e auditoria de fingerprints; portanto este resultado não é evidência preditiva final.",
        status=EvidenceStatus.PROTOTYPE,
        terms={
            "MAE": "Erro absoluto médio em pontos de popularity; menor é melhor.",
            "Artista não visto": "Nenhum artista do conjunto de teste aparece no conjunto de treino.",
        },
    )
    mo.vstack([
        mo.md("# Validação preditiva: popularity observada"),
        render_narrative_section(mo, narrative),
        mo.ui.table(summary),
        mo.md("MAE é a métrica primária; RMSE e R² são secundárias. Um ganho só será promovido após o protocolo completo confirmar redução mínima de 0,5 ponto e intervalo pareado por bootstrap agrupado que exclua zero."),
    ])
    return grouped, prepared, results, summary


@app.cell
def _(EvidenceStatus, NarrativeSection, mo, pl, prepared, render_narrative_section):
    collaboration = pl.DataFrame({
        "populacao": ["amostra modelada", "faixas de artista único", "faixas colaborativas incluídas"],
        "linhas": [prepared.height, prepared.height, 0],
        "uso": ["protótipo atual", "split primário", "pendente: estratos all/some/none seen"],
    })
    scope = NarrativeSection(
        title="Escopo atual das colaborações",
        question="Quais tipos de faixa estão representados no protótipo preditivo?",
        population="A amostra limitada usada pela execução preditiva acima.",
        unit="uma faixa canônica na amostra modelada",
        method="Contamos as faixas após restringir a população a um único artista, antes dos splits.",
        how_to_read="A tabela separa a amostra efetivamente modelada dos estratos de colaboração ainda pendentes.",
        denominator=f"{prepared.height:,} faixas modeladas nesta execução.".replace(",", "."),
        result="Nenhuma faixa colaborativa entra neste protótipo; os estratos all/some/none seen ainda não foram executados.",
        interpretation="O resultado atual mede apenas generalização entre faixas de artistas únicos.",
        use="Evitar que o protótipo seja apresentado como cobertura do catálogo completo e orientar a implementação dos estratos.",
        limitation="IDs, nomes, artista e álbum não são preditores. Features de artista/grafo exigem cálculo fold-local e OOV explícito.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"OOV": "Artista ou categoria não observado durante o treino."},
    )
    mo.vstack([mo.md("## Escopo e limites"), render_narrative_section(mo, scope), mo.ui.table(collaboration), mo.md("Esta entrega estima generalização contemporânea no snapshot; não prevê o próximo hit.")])
    return (collaboration,)


if __name__ == "__main__":
    app.run()
