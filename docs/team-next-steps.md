# Próximos passos do time

## Ponto de partida e gate

O ponto de partida comum é a `main` contendo o gate #77 (ordenação e amostragem determinísticas). Cada frente nasce dessa `main`, usa uma branch própria ligada à issue e abre um MR, preferencialmente Draft no início. A sequência de MRs é:

`associações → gêneros → clustering → predição → integração`.

Não promova números, rankings ou claims derivados antes de #77. Os branches/worktrees previstos são:

- `analysis/33-popularity-associations`: #31/#33 e Tasks de associações;
- `experiment/32-genre-structure`: #32 e representações, perfis e grafos de gênero;
- `experiment/35-clustering-gate`: #35 e PCA, loadings, clustering, estabilidade e null;
- `model/48-popularity-validation`: #41/#48 e validação preditiva, splits e fingerprints;
- `experiment/58-widget-utility`: laboratório dos widgets;
- `integrate/34-final-story`: integração final, exports e Molab.

Nenhum workstream paralelo edita `notebooks/spotify_analysis.py`; esse arquivo pertence exclusivamente ao integrador. Cada branch deve ser rebaseada na `main` antes do merge, com testes e HTML/manifest regenerados de forma determinística.

## Organização dos notebooks

Use a camada compartilhada de dados e não replique limpeza, schema ou DuckDB em células de experimento. O notebook de contrato/auditoria documenta a fonte, grain, contagens, ranges, duplicatas, conflitos e política de missingness. Os notebooks de frente consomem essa camada e repetem a cápsula de evidência, sem esconder a origem da população.

Os notebooks canônicos são:

- `notebooks/data_contract_audit.py`: contrato e qualidade;
- `notebooks/explorations/popularity_associations.py`: associações estatísticas e EDA de #31/#33;
- `notebooks/explorations/genre_representations.py`: multi-hot, PPMI/SVD, perfis e grafos de gênero;
- `notebooks/explorations/musical_structure.py`: PCA, loadings, K-means/GMM e estabilidade;
- `notebooks/explorations/popularity_validation.py`: baselines, splits group-aware, MAE e fingerprints;
- `notebooks/spotify_analysis.py`: somente apresentação de evidências revisadas e resultados promovidos.

O laboratório #58 e `experiment/46-rapid-triage` são Draft MRs/labs não integráveis. Servem para testar utilidade e registrar decisões; somente um veredito validado é portado para uma frente ou para o integrador. #81 (NMF/concept probes) e #78 (challengers neurais/concept bottleneck) são segunda onda e não bloqueiam o caminho crítico.

## Contratos de trabalho

Cada entrega deve declarar issue/spec, fixed point, branch, arquivos autorizados, não objetivos, população, grain, status da evidência, claim ceiling, critérios de aceite e testes. A comunicação nasce com o código: toda visualização principal informa pergunta, população/filtros, unidade, método intuitivo, como ler, denominador ou top-*n*, resultado desta execução, interpretação, uso e limite.

O notebook preditivo é o produtor canônico de `artifacts/evaluation/popularity_validation.json`, splits, métricas, intervalos e modelos promovidos. O integrador apenas carrega esse artefato por padrão e, mediante ação explícita, refaz somente os modelos promovidos; nunca substitui silenciosamente o artefato oficial. Claims devem distinguir associação, previsão contemporânea em held-out e causalidade.

Cada alteração de notebook atualiza HTML e `artifacts/notebooks/manifest.json`. O handoff Luna deve conter índice endereçável de issues, commits, paths/seções, artefatos, testes, pipeline, riscos, desvios e follow-ups. Sol é obrigatório apenas em mudanças de alto risco, conforme #68/#36, e audita specification, código, validade analítica e comunicação; a decisão de merge continua humana.

## Dependências, links e fluxo

Nesta assinatura do GitLab, dependências `blocks/is blocked by` não estão disponíveis. Usamos linked items `relates to`, checklist explícito no issue e `fluxo::bloqueado` para tornar o bloqueio visível. O checklist deve nomear o predecessor, o critério que libera a frente e o artefato esperado. Linked item não substitui child item: child representa decomposição de trabalho; link representa relação entre issues independentes.

As relações centrais são: #77 antes de #31/#32/#33/#35/#48; #47 antes de #32/#33/#48; #41 antes de #48; #42 antes de #32; #58 antes da decisão visual de #65; e #43/#36 antes do fechamento de #34. #31 relaciona-se a #33, sem ser forçada a child. As atribuições de lead e reviewer são feitas pelo time; autoria anterior não é atribuição automática.

Milestones representam resultados, não cada sessão ou horário. As três etapas são Fundação e contratos; Exploração, experimentos e seleção de evidências; e Análise validada e narrativa final. Datas ou checkpoints só devem ser registrados quando decididos pelo time; trabalho remoto flexível não deve virar deadline artificial. O milestone final vigente é o lugar para o resultado final, não para cada tarefa intermediária.

## Checklist antes de revisão

Execute `uv sync --frozen`, os testes definidos na issue, `uv run python scripts/render_notebooks.py`, `uv run python scripts/render_notebooks.py --check`, `marimo check` e o smoke top-to-bottom. Verifique translation pairs, outputs bounded, manifest, CI e Molab real; HTTP 200 de um preview não prova execução. Registre falhas com pipeline, SHA, job e primeiro trace.

Não feche issue nem marque `Finalizado` apenas porque o código existe. Exija critérios de aceite, CI, artefatos, caveats, handoff e revisão humana. O integrador é o último workstream e só deve incorporar evidência validada ou explicitamente rotulada como protótipo.
