"""Associações com popularity: confirmação pequena e screening controlado."""

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from hashlib import sha256
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
    import polars as pl
    import plotly.graph_objects as go
    import statsmodels.api as sm
    from spotify_data import EvidenceStatus, NarrativeSection, add_semantic_features, bh_fdr, build_data_layer, holm_adjust, render_narrative_section

    return EvidenceStatus, NarrativeSection, Path, add_semantic_features, bh_fdr, build_data_layer, go, holm_adjust, mo, np, pl, render_narrative_section, root, sha256, sm


@app.cell
def _(Path, build_data_layer, mo, root):
    csv_path = root / "data" / "raw" / "spotify_tracks.csv"
    mo.stop(not csv_path.exists(), mo.md(f"CSV não encontrado: `{csv_path}`"))
    layer = build_data_layer(csv_path)
    db = layer.connection
    tracks = db.execute("SELECT * FROM tracks ORDER BY track_id").pl()
    single = db.execute("""
        SELECT t.*, MIN(ta.artist) AS primary_artist
        FROM tracks t JOIN track_artists ta USING(track_id)
        GROUP BY ALL HAVING COUNT(DISTINCT ta.artist) = 1
    """).pl()
    return db, layer, single, tracks


@app.cell
def _(EvidenceStatus, NarrativeSection, go, mo, render_narrative_section, tracks):
    fig = go.Figure(go.Histogram(x=tracks["popularity"].to_numpy(), nbinsx=40))
    fig.update_layout(title="Distribuição da popularity canônica", xaxis_title="popularity", yaxis_title="faixas", height=380, template="plotly_white")
    zeros = int((tracks["popularity"] == 0).sum())
    mo.vstack([
        mo.md("# Popularity: associações observadas"),
        fig,
        mo.md(f"A métrica é contínua e observada no snapshot: mediana `{tracks['popularity'].median():.1f}`, zeros `{zeros:,}` e conflitos `{tracks.filter(tracks['popularity_conflict']).height:,}`. Isto não é forecasting temporal nem claim causal."),
        render_narrative_section(mo, NarrativeSection(
            title="Distribuição da popularity",
            question="Como a popularity observada se distribui no catálogo canônico?",
            population="Faixas canônicas disponíveis em `tracks`, com a regra de conflito já aplicada.",
            unit="Uma faixa canônica por observação do histograma.",
            method="O histograma agrupa o score observado em intervalos para mostrar concentração, zeros e amplitude.",
            how_to_read="O eixo x é o score de popularity; o eixo y é o número de faixas em cada intervalo.",
            denominator=f"O denominador é `{tracks.height:,}` faixas canônicas; conflitos são contabilizados separadamente.",
            result=f"A mediana é `{tracks['popularity'].median():.1f}`, com `{zeros:,}` zeros e `{tracks.filter(tracks['popularity_conflict']).height:,}` faixas conflitantes.",
            interpretation="A distribuição descreve o snapshot e ajuda a calibrar a leitura das associações; não mede sucesso futuro.",
            use="Contextualizar as associações e evitar interpretar popularity como sucesso futuro.",
            limitation="O score é observado no snapshot e não sustenta causalidade, comportamento de ouvintes ou forecasting temporal.",
            status=EvidenceStatus.PROTOTYPE,
            terms={
                "Popularity": "Score observado no dataset, de 0 a 100.",
                "Snapshot": "Retrato do catálogo no momento em que a fonte foi produzida.",
                "Faixa canônica": "Uma única linha analítica por track_id.",
            },
        )),
    ])
    return (fig,)


@app.cell
def _(EvidenceStatus, NarrativeSection, add_semantic_features, holm_adjust, mo, np, pl, render_narrative_section, sha256, single, sm):
    human = ["danceability", "energy", "valence", "acousticness", "instrumentalness", "speechiness"]
    controls = ["explicit", "key_sin", "key_cos", "mode", "time_signature", "log_duration_ms"]
    frame = add_semantic_features(single).drop_nulls([*human, *controls, "popularity", "primary_artist"])
    artists = frame["primary_artist"].to_list()
    split = np.array([int(sha256(str(artist).encode()).hexdigest(), 16) % 2 for artist in artists])
    confirmation = frame.filter(pl.Series("confirmation", split == 1))
    x_numeric = confirmation.select(human).to_numpy().astype(float)
    x_numeric = (x_numeric - x_numeric.mean(axis=0)) / np.where(x_numeric.std(axis=0) == 0, 1, x_numeric.std(axis=0))
    x_parts = [x_numeric, confirmation.select(["explicit", "key_sin", "key_cos", "mode", "log_duration_ms"]).to_numpy().astype(float)]
    time_values = confirmation["time_signature"].to_numpy()
    time_levels = sorted(set(time_values.tolist()))
    x_parts.append(np.column_stack([(time_values == level).astype(float) for level in time_levels[1:]]))
    x = sm.add_constant(np.column_stack(x_parts), has_constant="add")
    model = sm.OLS(confirmation["popularity"].to_numpy(), x).fit(cov_type="cluster", cov_kwds={"groups": confirmation["primary_artist"].to_numpy()})
    rows = []
    for index, _human_feature in enumerate(human, start=1):
        rows.append({"feature": _human_feature, "effect_per_sd": float(model.params[index]), "se_cluster": float(model.bse[index]), "p_value": float(model.pvalues[index])})
    association = pl.DataFrame(rows).with_columns(
        pl.Series("p_holm", holm_adjust([row["p_value"] for row in rows])),
    )
    association = association.with_columns((pl.col("effect_per_sd").abs() >= 1).alias("relevancia_pratica_1_pt"))
    omnibus = {"n_tracks": confirmation.height, "n_artists": confirmation["primary_artist"].n_unique(), "r_squared": float(model.rsquared), "family": "seis features, teste conjunto + Holm"}
    mo.vstack([
        mo.md("## 1. Família confirmatória: painel humano"),
        mo.ui.table(association.with_columns(pl.col(["effect_per_sd", "se_cluster", "p_value", "p_holm"]).round(4))),
        mo.ui.table(pl.DataFrame([omnibus])),
        render_narrative_section(mo, NarrativeSection(
            title="Família confirmatória: painel humano",
            question="Quais associações ajustadas aparecem entre as seis features centrais e popularity?",
            population="Tracks de artista único no subconjunto confirmation, separados por hash determinístico do artista.",
            unit="Uma faixa de artista único; erros-padrão agrupados por artista.",
            method="Um OLS ajustado estima efeitos por desvio-padrão das seis features, controles semânticos e categorias musicais; Holm ajusta a família principal.",
            how_to_read="`effect_per_sd` é a mudança estimada no score por 1 SD da feature, mantendo os demais termos do modelo; `p_holm` é o p-valor ajustado.",
            denominator=f"A análise usa `{confirmation.height:,}` tracks e `{confirmation['primary_artist'].n_unique():,}` artistas na partição confirmation.",
            result=f"O R² observado nesta execução é `{model.rsquared:.3f}`; a tabela mostra estimativas e incertezas, não causalidade.",
            interpretation="Os coeficientes são associações condicionais no snapshot, com incerteza agrupada por artista.",
            use="Selecionar hipóteses confirmatórias e orientar análises por gênero posteriores.",
            limitation="A partição discovery não seleciona hipóteses nesta implementação; generalização para artistas não vistos e heterogeneidade por gênero são follow-ups.",
            status=EvidenceStatus.PROTOTYPE,
            terms={
                "OLS": "Regressão linear que estima associações mantendo os demais termos constantes.",
                "Holm": "Correção que controla o erro da família de testes confirmatórios.",
                "Erro-padrão agrupado": "Incerteza que considera dependência entre faixas do mesmo artista.",
                "Confirmation": "Partição reservada para testar hipóteses previamente congeladas.",
            },
        )),
    ])
    return association, confirmation, frame, human, model, time_levels


@app.cell
def _(EvidenceStatus, NarrativeSection, association, bh_fdr, mo, np, pl, frame, human, render_narrative_section, sm):
    screen_rows = []
    for feature in human + ["loudness", "liveness", "tempo", "duration_ms"]:
        subset = frame.drop_nulls([feature])
        _screen_x = sm.add_constant(subset.select([feature]).to_numpy().astype(float), has_constant="add")
        fit = sm.OLS(subset["popularity"].to_numpy(), _screen_x).fit()
        screen_rows.append({"feature": feature, "p_value": float(fit.pvalues[1]), "effect": float(fit.params[1]), "n": subset.height})
    screening = pl.DataFrame(screen_rows).with_columns(pl.Series("p_bh", bh_fdr([row["p_value"] for row in screen_rows])))
    mo.vstack([
        mo.md("## 2. Screening exploratório"),
        mo.ui.table(screening.with_columns(pl.col(["p_value", "effect", "p_bh"]).round(4))),
        mo.md("O screening é gerador de hipótese e controla BH-FDR 0,05. A tabela não substitui a família confirmatória ajustada, a covariância agrupada nem a análise por gênero."),
        render_narrative_section(mo, NarrativeSection(
            title="Screening exploratório",
            question="Quais variáveis merecem investigação posterior?",
            population="Tracks de artista único disponíveis no frame analítico, avaliados feature a feature.",
            unit="Uma regressão simples por feature e população disponível.",
            method="O screening calcula associações individuais e aplica BH-FDR para controlar descobertas exploratórias.",
            how_to_read="Compare `effect`, `p_value` e `p_bh`; o screening não é equivalente ao modelo conjunto da seção anterior.",
            denominator="Cada linha informa seu próprio `n`, pois valores ausentes podem variar por feature.",
            result=f"Foram avaliadas `{len(screen_rows):,}` features; os efeitos são exploratórios e não foram promovidos a claims confirmatórios.",
            interpretation="O screening serve para priorizar perguntas, e seus p-valores ajustados não substituem um modelo confirmatório.",
            use="Gerar hipóteses para especificações futuras sem substituir confirmação pré-registrada.",
            limitation="Não há covariância agrupada nem heterogeneidade por gênero nesta tela; significância estatística isolada não implica importância prática.",
            status=EvidenceStatus.PROTOTYPE,
            terms={
                "Screening": "Busca exploratória de relações candidatas.",
                "BH-FDR": "Correção que limita a proporção esperada de falsos achados entre descobertas.",
                "Hipótese": "Proposição que exige um teste separado para confirmação.",
            },
        )),
    ])
    return (screening,)


@app.cell
def _(EvidenceStatus, NarrativeSection, association, mo, render_narrative_section, tracks):
    conflict_free = tracks.filter(~tracks["popularity_conflict"])
    mo.vstack([
        mo.md("## 3. Sensibilidades e teto de claims"),
        mo.ui.table(association),
        mo.md(f"Sensibilidade preparada: repetir os resultados na população sem os `{tracks.height - conflict_free.height}` conflitos. Outliers, zeros e duração longa devem ser preservados e testados com transformações robustas/log; não há remoção automática por IQR. Claims permitidos são associação ajustada e, em notebook próprio, previsão held-out; não causalidade, comportamento de ouvintes ou sucesso futuro."),
        render_narrative_section(mo, NarrativeSection(
            title="Sensibilidades e teto de claims",
            question="Quais ressalvas devem acompanhar qualquer claim sobre popularity?",
            population="A população canônica completa e a subpopulação sem conflitos, para comparação futura.",
            unit="Faixa canônica; conflitos, zeros e extremos são marcadores de sensibilidade.",
            method="Registramos a análise planejada para conflitos, outliers e transformações, sem executar ou apresentar esses resultados aqui.",
            how_to_read="A presença desta seção indica uma pergunta de robustez, não uma evidência já calculada.",
            denominator=f"A diferença potencial entre populações é `{tracks.height - conflict_free.height:,}` conflitos; a repetição ainda não foi executada.",
            result="Nenhuma sensibilidade adicional é declarada como resultado nesta execução.",
            interpretation="A transparência sobre análises ainda não executadas é parte do limite da evidência atual.",
            use="Impedir extrapolação dos resultados exploratórios e orientar o protocolo estatístico futuro.",
            limitation="Não há evidência de robustez a conflitos, outliers ou transformações até que o follow-up seja executado.",
            status=EvidenceStatus.PROTOTYPE,
            terms={
                "Sensibilidade": "Repetição que testa se uma decisão analítica altera o resultado.",
                "Outlier": "Valor extremo preservado até haver evidência de erro.",
                "Claim ceiling": "Limite máximo do que o desenho permite afirmar.",
                "Held-out": "Dados mantidos fora do ajuste e usados apenas para avaliação.",
            },
        )),
    ])
    return


if __name__ == "__main__":
    app.run()
