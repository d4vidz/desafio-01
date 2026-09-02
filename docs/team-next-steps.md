# Próximos passos para o time

## Ponto de partida comum

Depois que o MR de fundação entrar em `main`, toda pessoa começa atualizando `main`, criando uma branch curta ligada à sua issue e executando `uv sync --frozen`. O CSV bruto permanece imutável. Todos os notebooks chamam `spotify_data.build_data_layer`, que reconstrói `tracks_raw`, `tracks_clean`, `tracks`, `track_genres` e `track_artists` e fornece o mesmo report de contrato; não copie a limpeza para células novas nem gere um CSV limpo alternativo.

## Como assumir uma frente

1. Escolha uma issue com escopo e critério de aceite suficientes; registre lead e reviewer.
2. Crie `feature/<iid>-<resumo>`, `experiment/<iid>-<resumo>` ou outra branch prevista em `docs/branching.md`.
3. Use o notebook canônico da frente: `data_contract_audit.py` para contrato, `explorations/popularity_associations.py` para associações estatísticas, `explorations/genre_representations.py` para representações/grafos de gênero, `explorations/musical_structure.py` para PCA/clustering e `explorations/popularity_validation.py` para modelos held-out. Código compartilhado e regras de dados ficam em módulos, não duplicados entre notebooks.
4. Registre pergunta, grain, features, split, métricas, outputs esperados e caveats antes de interpretar resultados.
5. Abra um Draft MR cedo, use `Refs #IID` e não feche a issue antes da revisão e da definition of done.

## Frentes atuais

- qualidade e contrato: reconciliar a limpeza auditada, ranges, conflitos de popularidade e source-to-clean counts;
- EDA e estatística: distribuições, heterogeneidade por gênero, effect sizes e múltiplos testes;
- estrutura musical: PCA, loadings, estabilidade de clustering e relação com gêneros;
- modelagem: baselines de popularidade, fingerprints de artista e splits group-aware;
- grafos: sobreposição entre gêneros e ablations incrementais, sem graph database;
- integração: selecionar apenas evidências revisadas para `notebooks/spotify_analysis.py`.

O protocolo de representação categórica está versionado em `docs/categorical-representation.md` e aparece como ladder exploratório em `genre_representations.py`. Não inicie uma implementação neural: o experimento aprovado é PPMI + TruncatedSVD, com ajuste fold-local na predição.

## Antes de pedir revisão

Execute os comandos de `docs/ci.md`, regenere os snapshots com `uv run python scripts/render_notebooks.py`, confira `uv run python scripts/render_notebooks.py --check`, outputs bounded e escreva uma conclusão que distinga associação, previsão contemporânea e causalidade. Se o CI falhar, registre pipeline, SHA, jobs e primeiro trace; falha sem job não é evidência de código quebrado. O smoke headless executa cada notebook por exportação HTML temporária; os snapshots revisáveis ficam em `artifacts/notebooks/html/`.
