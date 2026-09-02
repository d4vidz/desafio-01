# Contrato de papéis das features v0.1

Este documento orienta o primeiro ciclo de análise. Ele não elimina colunas do CSV e não declara que uma feature é causalmente relevante. Ele separa o que merece interpretação humana imediata do que deve permanecer disponível para experimentos automatizados.

## Outcome e grain

- Outcome principal: `popularity` observada no catálogo.
- Grain principal: uma linha canônica por `track_id`.
- `popularity` nunca entra como preditor da própria tarefa.
- IDs, nomes de faixa, nomes de artista e campos identificadores são contexto, não preditores diretos.

## Papéis v0.1

| Papel | Colunas | Uso |
| --- | --- | --- |
| Painel humano | `danceability`, `energy`, `valence`, `acousticness`, `instrumentalness`, `speechiness` | Associações, comparações e narrativa principal sobre popularity. |
| Sensibilidade/contexto | `loudness`, `liveness`, `tempo`, `duration_ms` | Repetições, controle de redundância e pool automatizado. |
| Categóricas | `explicit`, `key`, `mode`, `time_signature` | Comparações e codificação categórica; não misturar silenciosamente com correlações contínuas. |
| Agrupamento/contexto | `artists`, `track_genre`, `album_name`, `track_name` | Grain, estratificação, validação, joins e interpretação contextual. |
| Candidatas automatizadas | Todas as audio features e categóricas válidas | Seleção regularizada, permutation importance e estabilidade held-out. |
| Derivadas controladas | Agregados de artista e grafo | Apenas ablation fold-local, com fallback explícito para artistas não vistos. |

## Protocolo de evidência

1. O painel humano usa effect sizes, intervalos e heterogeneidade por gênero; p-values isolados não selecionam features.
2. Hipóteses primárias usam discovery/confirmation agrupado por artista.
3. Screening exploratório declara multiplicidade e usa FDR quando apropriado.
4. O claim preditivo é estimativa de popularity observada em dados held-out, não forecasting temporal.
5. Split aleatório por faixa é somente diagnóstico otimista; unseen-artist é o split principal.
6. Nenhuma feature é removida permanentemente por este contrato. Mudanças exigem registro de evidência, impacto e trabalho removido ou adiado.

## Hipóteses iniciais

- As associações das features do painel humano com popularity podem ser pequenas e heterogêneas entre gêneros.
- `energy`, `loudness` e `acousticness` devem ser tratados como bloco potencialmente redundante.
- O áudio pode carregar fingerprints de artista mesmo sem o nome do artista; por isso random split não é evidência suficiente de generalização.
- Features derivadas de grafos só entram na narrativa se melhorarem a métrica held-out no mesmo split e modelo.
