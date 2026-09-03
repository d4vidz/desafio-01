# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "duckdb>=1.1,<2", "marimo>=0.14,<1", "matplotlib>=3.9,<4",
#   "numpy>=2,<3", "pandas>=2.2,<4", "plotly>=5.24,<7", "polars>=1.20,<2",
#   "pyarrow>=18,<25", "scikit-learn>=1.5,<2", "statsmodels>=0.14,<1",
#   "wigglystuff>=0.5.21,<0.6",
# ]
# ///

"""Auditoria reproduzível do contrato e da reconstrução DuckDB."""

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
        snapshot = "0ac3efc5133fa6481519a2a373134c9e6f50689c"
        snapshot_root = root / f"desafio-01-{snapshot}"
        if not snapshot_root.exists():
            archive_path = root / f"desafio-01-{snapshot}.zip"
            urlretrieve(f"https://github.com/d4vidz/desafio-01/archive/{snapshot}.zip", archive_path)
            with ZipFile(archive_path) as archive:
                archive.extractall(root)
        root = snapshot_root
    if not (root / "spotify_data").exists():
        root = Path(__file__).resolve().parents[1]
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
    from spotify_data import EvidenceStatus, NarrativeSection, build_data_layer, contract_capsule, load_tracks_raw, render_narrative_section

    return EvidenceStatus, NarrativeSection, Path, build_data_layer, contract_capsule, load_tracks_raw, mo, pl, render_narrative_section, root


@app.cell
def _(Path, build_data_layer, load_tracks_raw, mo, root):
    csv_path = root / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    raw = load_tracks_raw(csv_path)
    report = layer.report
    return csv_path, layer, raw, report


@app.cell
def _(EvidenceStatus, NarrativeSection, mo, render_narrative_section):
    introduction = NarrativeSection(
        title="Auditoria do contrato de dados",
        question="O que esta auditoria garante antes das análises?",
        population="O snapshot CSV disponível no repositório e suas relações derivadas.",
        unit="Linha física do CSV, faixa canônica e aresta faixa–gênero.",
        method="Reconstruímos a camada DuckDB efêmera e calculamos o relatório do contrato a partir da fonte.",
        how_to_read="Use a cápsula para confirmar fonte, versão e status; depois leia as tabelas de reconciliação para entender cada grain.",
        denominator="As contagens são exibidas por relação; não compare linhas físicas diretamente com faixas sem considerar a deduplicação.",
        result="A auditoria apresenta evidência dinâmica da execução atual.",
        interpretation="A camada padroniza a entrada dos experimentos, mas seus checks não validam claims analíticos ou validade externa.",
        use="Servir de ponto de partida comum para os demais notebooks e detectar drift da camada de dados.",
        limitation="Esta auditoria não prova validade externa, causalidade ou representatividade do snapshot.",
        status=EvidenceStatus.INFRASTRUCTURE,
        terms={
            "Grain": "A unidade representada por cada linha, como linha física, faixa ou relação.",
            "Contrato": "Regras versionadas que todas as análises devem respeitar.",
            "DuckDB efêmero": "Banco em memória reconstruído do CSV a cada runtime.",
            "Muitos-para-muitos": "Uma faixa pode ter vários gêneros, e um gênero reúne várias faixas.",
        },
    )
    mo.vstack([
        mo.md("""
    # Auditoria do contrato de dados

    Esta é a única etapa que detalha a reconstrução. Os demais notebooks
    consomem as mesmas tabelas e exibem uma cápsula compacta, evitando drift de
    limpeza e payloads grandes.
    """),
        render_narrative_section(mo, introduction),
    ])
    return


@app.cell
def _(EvidenceStatus, NarrativeSection, contract_capsule, mo, pl, render_narrative_section, report):
    capsule = pl.DataFrame([contract_capsule(report)])
    mo.vstack([
        mo.md("## 1. Cápsula de execução"),
        mo.ui.table(capsule),
        mo.md(f"Revisão do código: `{report.code_revision.get('git_commit') or 'não informada'}`; ambiente `{report.code_revision['python']}`."),
        render_narrative_section(mo, NarrativeSection(
            title="Cápsula de execução",
            question="Qual versão da camada foi executada?",
            population="A execução atual de `build_data_layer()` sobre o CSV configurado.",
            unit="Uma execução da camada e seu relatório de contrato.",
            method="A cápsula resume hash, versão, contagens e status calculados pelo relatório.",
            how_to_read="Confira o hash da fonte, a versão do contrato e o status antes de interpretar qualquer tabela posterior.",
            denominator="Os denominadores são as contagens reportadas para cada grain da camada.",
            result=f"O status desta execução é `{report.status}`; a revisão Git registrada é `{report.code_revision.get('git_commit') or 'não informada'}`.",
            interpretation="A cápsula torna a execução identificável, mas não transforma a camada em evidência sobre o mundo externo.",
            use="Permitir que outra pessoa reconstrua e compare a mesma camada.",
            limitation="A revisão local pode não estar disponível fora de CI; isso deve permanecer visível como limitação.",
            status=EvidenceStatus.INFRASTRUCTURE,
            terms={
                "Hash": "Assinatura do conteúdo usada para identificar exatamente a fonte.",
                "Versão do contrato": "Identificador das regras de reconstrução aplicadas.",
                "Proveniência": "Registro da origem, revisão e ambiente da execução.",
            },
        )),
    ])
    return capsule


@app.cell
def _(EvidenceStatus, NarrativeSection, mo, pl, raw, render_narrative_section, report):
    counts = pl.DataFrame({"relação": list(report.counts), "linhas": list(report.counts.values())})
    missing = pl.DataFrame(report.missingness).filter(pl.col("missing_count") > 0)
    if missing.is_empty():
        missing = pl.DataFrame({"resultado": ["nenhum missingness nos identificadores auditados"]})
    ranges = pl.DataFrame([
        {"campo": field, **values}
        for field, values in report.ranges.items()
        if field != "invalid_counts"
    ])
    invalid = pl.DataFrame([
        {"regra": field, "linhas_invalidas": value}
        for field, value in report.ranges["invalid_counts"].items()
    ])
    sentinels = pl.DataFrame([
        {"regra": field, "linhas": value}
        for field, value in report.ranges["sentinel_counts"].items()
    ])
    removals = pl.DataFrame([{"tratamento": key, "linhas": value} for key, value in report.removals.items()])
    mo.vstack([
        mo.md("## 2. Reconciliação source → clean → canonical"),
        mo.hstack([mo.ui.table(counts), mo.ui.table(removals)], widths="equal"),
        mo.md("A linha física do CSV é preservada em `tracks_raw`; limpeza e deduplicação são reproduzidas em memória. `track_id` repetido não é erro por si só: gênero é uma relação many-to-many."),
        mo.hstack([mo.ui.table(missing), mo.ui.table(ranges)], widths="equal"),
        mo.hstack([mo.vstack([mo.md("### Regras de range"), mo.ui.table(invalid)]), mo.vstack([mo.md("### Sentinelas para decisão"), mo.ui.table(sentinels)])], widths="equal"),
        render_narrative_section(mo, NarrativeSection(
            title="Reconciliação dos grains",
            question="O que mudou entre a fonte, a tabela limpa e a tabela canônica?",
            population="Todas as linhas carregadas do CSV e as relações reconstruídas pela camada.",
            unit="Linha, faixa ou relação, conforme o quadro apresentado.",
            method="Comparamos contagens, missingness, remoções, ranges e sentinelas sem alterar o CSV original.",
            how_to_read="Leia cada tabela junto do título: `tracks_raw` representa linhas físicas; `tracks` representa faixas; arestas podem repetir uma faixa por gênero.",
            denominator="Cada taxa ou contagem deve usar o grain indicado na própria tabela.",
            result=f"A execução reporta `{report.counts.get('tracks_raw', 0):,}` linhas raw e `{report.counts.get('tracks', 0):,}` faixas canônicas.",
            interpretation="A mesma faixa pode aparecer em mais de uma relação de gênero; portanto, contagens de arestas não são contagens de faixas.",
            use="Evitar comparações com denominador implícito e tornar remoções auditáveis.",
            limitation="Valores extremos sinalizados não são automaticamente erros e não são removidos por esta etapa.",
            status=EvidenceStatus.INFRASTRUCTURE,
            terms={
                "tracks_raw": "Uma linha para cada linha física preservada do CSV.",
                "tracks": "Uma linha canônica para cada track_id.",
                "track_genres": "Uma aresta para cada associação faixa–gênero.",
                "Denominador": "População usada como base de uma contagem ou taxa.",
            },
        )),
    ])
    return counts, invalid, missing, ranges, removals, sentinels


@app.cell
def _(EvidenceStatus, NarrativeSection, mo, pl, render_narrative_section, report):
    conflicts = pl.DataFrame([{"campo": key, "ocorrencias": value} for key, value in report.conflicts.items()])
    mo.vstack([
        mo.md("## 3. Conflitos, missingness e política"),
        mo.ui.table(conflicts),
        mo.md("Não há imputação aplicada ao snapshot: missingness real de features não foi observado. O notebook de associações preserva conflitos de `popularity` como mediana + min/max/range e repete headlines sem os conflitos como sensibilidade."),
        render_narrative_section(mo, NarrativeSection(
            title="Conflitos e política de qualidade",
            question="Quais problemas de qualidade ainda exigem cautela analítica?",
            population="Campos e regras de qualidade definidos no contrato.",
            unit="Ocorrência de conflito, missingness, sentinel ou violação de range.",
            method="Apresentamos as ocorrências detectadas e separamos tratamento aplicado de sensibilidade futura.",
            how_to_read="Uma tabela vazia de missingness significa que nenhum missing foi detectado nos campos auditados, não que todo risco foi eliminado.",
            denominator="As ocorrências são contadas no grain correspondente à regra; não são taxas populacionais universais.",
            result=f"A execução encontrou `{len(report.conflicts):,}` tipos de conflito reportados e não aplicou imputação real.",
            interpretation="Ausência de missingness detectado reduz uma fonte de risco, mas não elimina incertezas de origem, cobertura ou semântica.",
            use="Orientar análises de sensibilidade e limitar claims ao snapshot observado.",
            limitation="Sensibilidades sem execução nesta célula não constituem resultados; extremos e conflitos continuam requerendo análise posterior.",
            status=EvidenceStatus.INFRASTRUCTURE,
            terms={
                "Missingness": "Ausência registrada de um valor esperado.",
                "Conflito": "Valores divergentes para um campo que deveria ser canônico.",
                "Outlier": "Valor extremo que requer investigação, sem ser erro por definição.",
                "Imputação": "Substituição de valor ausente por uma estimativa.",
            },
        )),
    ])
    return (conflicts,)


if __name__ == "__main__":
    app.run()
