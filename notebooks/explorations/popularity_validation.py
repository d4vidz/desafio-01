# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "duckdb>=1.1,<2", "marimo>=0.14,<1", "matplotlib>=3.9,<4",
#   "numpy>=2,<3", "pandas>=2.2,<4", "plotly>=5.24,<7", "polars>=1.20,<2",
#   "pyarrow>=18,<25", "scikit-learn>=1.5,<2", "statsmodels>=0.14,<1",
#   "wigglystuff>=0.5.21,<0.6",
# ]
# ///

"""Validation of observed popularity with unseen-artist splits."""

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

    root = Path.cwd()
    bundle_path = root / "spotify_molab_bundle.zip"
    if not (root / "spotify_data").exists() and bundle_path.exists():
        with ZipFile(bundle_path) as bundle:
            bundle.extractall(root)
    if not (root / "spotify_data").exists():
        snapshot = "efffedc30baeb5beb21603f3c1fedefcaad182b4"
        snapshot_root = root / f"desafio-01-{snapshot}"
        if not snapshot_root.exists():
            archive_path = root / f"desafio-01-{snapshot}.zip"
            urlretrieve(f"https://github.com/d4vidz/desafio-01/archive/{snapshot}.zip", archive_path)
            with ZipFile(archive_path) as archive:
                archive.extractall(root)
        root = snapshot_root
    if not (root / "spotify_data").exists():
        root = Path(__file__).resolve().parents[2]
    csv_snapshot = root / "data" / "raw" / "spotify_tracks.csv"
    expected_source = "1a769bbbbb2fa4451d4309248349799ce8ab5efc21e053e2bb3aa28ddcb53d83"
    if csv_snapshot.exists():
        observed_source = sha256(csv_snapshot.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if observed_source != expected_source:
            raise RuntimeError("O snapshot Molab não corresponde ao hash canônico do CSV.")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import marimo as mo
    import polars as pl
    from spotify_data import (
        EvidenceStatus,
        NarrativeSection,
        add_semantic_features,
        build_data_layer,
        diagnose_audio_neighbours,
        deterministic_sample,
        render_narrative_section,
    )
    from spotify_data.evaluation import (
        EvaluationSpec,
        best_model_summary,
        run_evaluation,
    )
    return (EvidenceStatus, NarrativeSection, Path, add_semantic_features,
            EvaluationSpec, best_model_summary, build_data_layer,
            diagnose_audio_neighbours, deterministic_sample, mo, pl, render_narrative_section, root,
            run_evaluation)


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
def _(EvidenceStatus, EvaluationSpec, NarrativeSection, add_semantic_features,
      best_model_summary, deterministic_sample, model_frame, mo, pl,
      render_narrative_section, run_evaluation):
    numeric = ["danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo", "log_duration_ms", "key_sin", "key_cos", "explicit_binary", "mode_binary"]
    prepared = add_semantic_features(model_frame)
    # A deterministic cap keeps the exploratory notebook responsive. The
    # final run can remove the cap without changing the split/model protocol.
    prepared = deterministic_sample(prepared, 40_000, seed=2026)
    evaluation = run_evaluation(
        prepared,
        EvaluationSpec(tuple(numeric), repeats=5, seed=2026),
    )
    summary = evaluation.summary
    grouped = summary.filter(pl.col("split") == "artista não visto")
    best = best_model_summary(summary, "artista não visto")
    narrative = NarrativeSection(
        title="Validação preditiva da popularidade observada",
        question="As audio features generalizam para faixas de artistas que não aparecem no treino?",
        population=f"{prepared.height:,} faixas de artista único do snapshot".replace(",", "."),
        unit="uma faixa canônica",
        method="Comparamos uma baseline de mediana e modelos de regressão no split principal por artista não visto; o split aleatório serve apenas como diagnóstico otimista.",
        how_to_read="Compare o MAE entre modelos dentro do split principal: menor erro é melhor. A tabela também mostra RMSE e R² como métricas secundárias.",
        denominator=f"{grouped.height} combinações de modelo no resumo; cinco repetições 80/20 por artista.",
        result=f"O menor MAE médio observado no split por artista foi {best.mae_mean:.2f}, para o modelo {best.model}.",
        interpretation="Este é um diagnóstico de generalização contemporânea no snapshot, não uma previsão temporal de sucesso futuro.",
        use="Orientar a especificação dos experimentos preditivos e a escolha de ablações que serão validadas em uma entrega posterior.",
        limitation="O intervalo pareado já é calculado por bootstrap de artistas, mas ainda faltam estratos de colaboração e auditoria de fingerprints; portanto este resultado não é evidência preditiva final.",
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
        mo.md("## Incerteza pareada e auditoria das partições"),
        mo.ui.table(evaluation.paired_intervals),
        mo.ui.table(evaluation.partitions),
        mo.md("MAE é a métrica primária; RMSE e R² são secundárias. `delta_mae` compara cada modelo à baseline de mediana: valores negativos favorecem o modelo. `promotion_gate` só é verdadeiro quando o ganho médio é de pelo menos 0,5 ponto e o intervalo de 95% exclui zero. A tabela de partições deve mostrar sobreposição de artistas igual a zero no split principal."),
    ])
    return evaluation, grouped, prepared, summary


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


@app.cell
def _(EvidenceStatus, NarrativeSection, diagnose_audio_neighbours, mo, pl, prepared, render_narrative_section):
    fingerprint_features = (
        "danceability", "energy", "loudness", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence", "tempo", "log_duration_ms",
    )
    overall_fingerprint = diagnose_audio_neighbours(
        prepared,
        feature_columns=fingerprint_features,
        artist_column="primary_artist",
        genre_column=None,
        duplicate_tolerance=0.0,
        max_queries=200,
        max_candidates=10_000,
        seed=2026,
    )
    within_genre_fingerprint = diagnose_audio_neighbours(
        prepared,
        feature_columns=fingerprint_features,
        artist_column="primary_artist",
        genre_column="representative_track_genre",
        duplicate_tolerance=1e-6,
        same_genre=True,
        max_queries=200,
        max_candidates=10_000,
        seed=2026,
    )
    fingerprint_summary = pl.concat(
        [
            overall_fingerprint.summary.with_columns(pl.lit("catálogo; vetores exatos").alias("probe")),
            within_genre_fingerprint.summary.with_columns(pl.lit("mesmo gênero representativo; near-duplicates").alias("probe")),
        ],
        how="diagonal_relaxed",
    ).select("probe", pl.all().exclude("probe"))
    changed_examples = overall_fingerprint.audit.filter(
        pl.col("before_same_artist") != pl.col("after_same_artist")
    ).head(10)
    overall_before_n = overall_fingerprint.summary[0, "before_eligible_queries"]
    overall_after_n = overall_fingerprint.summary[0, "after_eligible_queries"]
    within_genre_before_n = within_genre_fingerprint.summary[0, "before_eligible_queries"]
    within_genre_after_n = within_genre_fingerprint.summary[0, "after_eligible_queries"]
    fingerprint_narrative = NarrativeSection(
        title="Auditoria exploratória de fingerprints de artista",
        question="O vizinho acústico mais próximo tende a ser do mesmo artista, e essa taxa muda ao remover vetores duplicados?",
        population="Uma amostra seeded de até 10.000 faixas de artista único; 200 consultas por probe.",
        unit="uma faixa consultada e seu vizinho mais próximo",
        method="Padronizamos dez audio features, buscamos o vizinho euclidiano e comparamos a taxa de mesmo artista antes/depois de excluir vetores exatos; repetimos dentro do gênero representativo com tolerância near-duplicate de 1e-6 nas features originais.",
        how_to_read="Uma queda forte após exclusão sugere que duplicatas explicavam parte do fingerprint; taxa persistente sugere assinatura acústica ou estrutura de catálogo a investigar.",
        denominator=f"No probe geral, {overall_before_n} consultas compõem a taxa anterior e {overall_after_n} a posterior, sobre {overall_fingerprint.summary[0, 'candidate_rows']} candidatos. No probe por gênero, os denominadores são {within_genre_before_n} e {within_genre_after_n}, sobre {within_genre_fingerprint.summary[0, 'candidate_rows']} candidatos. Consultas sem candidato posterior são contadas separadamente.",
        result=f"No probe geral, a taxa foi {overall_fingerprint.summary[0, 'before_same_artist_rate']:.3f} antes e {overall_fingerprint.summary[0, 'after_same_artist_rate']:.3f} após excluir vetores exatos.",
        interpretation="O diagnóstico mede recuperabilidade contemporânea de artista no espaço acústico, não usa artista como preditor de popularity.",
        use="Comparar o split aleatório com artista não visto e orientar ablations de leakage em #63.",
        limitation="É uma amostra bounded; gênero representativo reduz memberships múltiplas a uma tag e a tolerância near-duplicate requer sensibilidade antes de promoção.",
        status=EvidenceStatus.PROTOTYPE,
        terms={"fingerprint": "padrão acústico que pode tornar o artista reconhecível", "near-duplicate": "vetor de áudio quase idêntico dentro de tolerância explícita"},
    )
    mo.vstack([
        mo.md("## Auditoria de fingerprints"),
        render_narrative_section(mo, fingerprint_narrative),
        mo.ui.table(fingerprint_summary),
        mo.md("### Exemplos em que a exclusão alterou o indicador de mesmo artista"),
        mo.ui.table(changed_examples),
    ])
    return fingerprint_summary, overall_fingerprint, within_genre_fingerprint


if __name__ == "__main__":
    app.run()
