"""Auditoria reproduzível do contrato e da reconstrução DuckDB."""

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
        root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import marimo as mo
    import polars as pl
    from spotify_data import build_data_layer, contract_capsule, load_tracks_raw

    return Path, build_data_layer, contract_capsule, load_tracks_raw, mo, pl, root


@app.cell
def _(Path, build_data_layer, load_tracks_raw, mo, root):
    csv_path = root / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    raw = load_tracks_raw(csv_path)
    report = layer.report
    return csv_path, layer, raw, report


@app.cell
def _(mo):
    mo.md("""
    # Auditoria do contrato de dados

    Esta é a única etapa que detalha a reconstrução. Os demais notebooks
    consomem as mesmas tabelas e exibem uma cápsula compacta, evitando drift de
    limpeza e payloads grandes.
    """)
    return


@app.cell
def _(contract_capsule, mo, pl, report):
    capsule = pl.DataFrame([contract_capsule(report)])
    mo.vstack([
        mo.md("## 1. Cápsula de execução"),
        mo.ui.table(capsule),
        mo.md(f"Revisão do código: `{report.code_revision.get('git_commit') or 'não informada'}`; ambiente `{report.code_revision['python']}`."),
    ])
    return capsule


@app.cell
def _(mo, pl, raw, report):
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
    ])
    return counts, invalid, missing, ranges, removals, sentinels


@app.cell
def _(mo, pl, report):
    conflicts = pl.DataFrame([{"campo": key, "ocorrencias": value} for key, value in report.conflicts.items()])
    mo.vstack([
        mo.md("## 3. Conflitos, missingness e política"),
        mo.ui.table(conflicts),
        mo.md("Não há imputação aplicada ao snapshot: missingness real de features não foi observado. O notebook de associações preserva conflitos de `popularity` como mediana + min/max/range e repete headlines sem os conflitos como sensibilidade."),
    ])
    return (conflicts,)


if __name__ == "__main__":
    app.run()
