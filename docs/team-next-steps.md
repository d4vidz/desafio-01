# Próximos passos para o time

## Ponto de partida comum

Depois que o MR de fundação entrar em `main`, toda pessoa começa atualizando `main`, criando uma branch curta ligada à sua issue e executando `uv sync --frozen`. O CSV bruto permanece imutável. Todos os notebooks chamam `spotify_data.build_duckdb_layer`, que reconstrói `tracks_raw`, `tracks_clean`, `tracks`, `track_genres` e `track_artists`; não copie a limpeza para células novas nem gere um CSV limpo alternativo.

## Como assumir uma frente

1. Escolha uma issue com escopo e critério de aceite suficientes; registre lead e reviewer.
2. Crie `feature/<iid>-<resumo>`, `experiment/<iid>-<resumo>` ou outra branch prevista em `docs/branching.md`.
3. Use um notebook em `notebooks/explorations/` para uma família de pergunta ou experimento. Código compartilhado e regras de dados ficam em módulos, não duplicados entre notebooks.
4. Registre pergunta, grain, features, split, métricas, outputs esperados e caveats antes de interpretar resultados.
5. Abra um Draft MR cedo, use `Refs #IID` e não feche a issue antes da revisão e da definition of done.

## Frentes atuais

- qualidade e contrato: reconciliar a limpeza auditada, ranges, conflitos de popularidade e source-to-clean counts;
- EDA e estatística: distribuições, heterogeneidade por gênero, effect sizes e múltiplos testes;
- estrutura musical: PCA, loadings, estabilidade de clustering e relação com gêneros;
- modelagem: baselines de popularidade, fingerprints de artista e splits group-aware;
- grafos: sobreposição entre gêneros e ablations incrementais, sem graph database;
- integração: selecionar apenas evidências revisadas para `notebooks/spotify_analysis.py`.

Ainda precisam entrar no backlog uma especificação de representação das categóricas e uma entrega para comparar one-hot, multi-hot e embeddings de gênero. Essas issues serão fechadas no próximo grilling; não inicie uma implementação neural antes de o objetivo e o protocolo de avaliação serem definidos.

## Antes de pedir revisão

Execute os comandos de `docs/ci.md`, confira outputs bounded e escreva uma conclusão que distinga associação, previsão contemporânea e causalidade. Se o CI falhar, registre pipeline, SHA, jobs e primeiro trace; falha sem job não é evidência de código quebrado.
