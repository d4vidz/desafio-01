# Próximos passos do time

## Ponto de partida e objetivo

O ponto de partida comum é a `main` contendo o gate #77 (ordenação e amostragem determinísticas). O ciclo será concluído por critérios de aceite, sem criar um novo prazo. A entrega principal reúne associações, representações de gênero, estrutura musical, três baselines preditivos e uma integração revisada.

Cada frente nasce dessa `main`, usa uma branch própria ligada à issue e abre um MR, preferencialmente Draft no início. Associações, gêneros, clustering e predição podem trabalhar em paralelo depois que os contratos necessários estiverem aprovados. A ordem de merge é um mecanismo de integração e revisão; ela não transforma essas frentes em dependências analíticas entre si.

As branches/worktrees previstas são:

- `analysis/33-popularity-associations`: #31/#33 e Tasks de associações;
- `experiment/32-genre-structure`: #32 e representações, perfis, overlap e grafos de gênero;
- `experiment/35-clustering-gate`: #35 e PCA, loadings, clustering, estabilidade e null;
- `model/48-popularity-validation`: #41/#48 e validação preditiva, splits e fingerprints;
- `experiment/58-widget-utility`: laboratório dos widgets;
- `integrate/34-final-story`: integração final, exports e Molab.

Nenhum workstream paralelo edita `notebooks/spotify_analysis.py`; esse arquivo pertence exclusivamente ao integrador. Cada branch deve ser rebaseada na `main` antes do merge, com testes e HTML/manifest regenerados de forma determinística. Não promova números, rankings ou claims derivados antes de #77.

## Organização dos notebooks e das issues

Use a camada compartilhada de dados e não replique limpeza, schema ou DuckDB em células de experimento. O notebook de contrato/auditoria documenta a fonte, grain, contagens, ranges, duplicatas, conflitos e política de missingness. Os notebooks de frente consomem essa camada e repetem a cápsula de evidência, sem esconder a origem da população.

Os notebooks canônicos são:

- `notebooks/data_contract_audit.py`: contrato e qualidade;
- `notebooks/explorations/popularity_associations.py`: associações estatísticas e EDA de #31/#33;
- `notebooks/explorations/genre_representations.py`: multi-hot, PPMI/SVD, perfis e grafos de gênero;
- `notebooks/explorations/musical_structure.py`: PCA, loadings, K-means/GMM e estabilidade;
- `notebooks/explorations/popularity_validation.py`: baselines, splits group-aware, MAE e fingerprints;
- `notebooks/spotify_analysis.py`: somente apresentação de evidências revisadas e resultados promovidos.

#48 concentra o programa e o benchmark preditivo. #75 produz o notebook canônico e o handoff dos resultados, sem duplicar a busca experimental. #78 é um piloto delimitado para comparar gated multi-hot com embedding 16D e medir ganho preditivo. #81 recebe posteriormente NMF e concept probes. #32 concentra representações, perfis, overlap e visualizações; #58 testa a utilidade dos widgets antes de qualquer promoção.

O laboratório #58 e `experiment/46-rapid-triage` são Draft MRs/labs não integráveis. Servem para testar utilidade e registrar decisões; somente um veredito validado é portado para uma frente ou para o integrador.

## Contratos de trabalho e critérios de fluxo

Cada entrega deve declarar issue/spec, fixed point, branch, arquivos autorizados, não objetivos, população, grain, status da evidência, claim ceiling, critérios de aceite e testes. A comunicação nasce com o código: toda visualização principal informa pergunta, população/filtros, unidade, método intuitivo, como ler, denominador ou top-*n*, resultado desta execução, interpretação, uso e limite.

O notebook preditivo é o produtor canônico de `artifacts/evaluation/popularity_validation.json`, splits, métricas, intervalos e modelos promovidos. O integrador apenas carrega esse artefato por padrão e, mediante ação explícita, refaz somente os modelos promovidos; nunca substitui silenciosamente o artefato oficial. Claims devem distinguir associação, previsão contemporânea em held-out e causalidade.

Uma specification aberta não equivale a uma specification não aprovada. O estado de aprovação deve ser registrado por versão, com a decisão e a data no issue ou MR correspondente. Código existente também não implica aceite: a issue só avança quando os critérios definidos forem satisfeitos.

Use `fluxo::bloqueado` somente quando houver um predecessor nomeado, uma condição objetiva de liberação e o artefato esperado. Use `fluxo::revisão` somente quando houver uma entrega concreta revisável. Uma dependência técnica pode coexistir com trabalho exploratório paralelo; o bloqueio deve indicar o que realmente está impedido.

As atribuições de lead e reviewer são feitas pelos humanos do time. A autoria anterior não é atribuição automática. Cada workstream entrega índice de issues, commits, paths/seções, artefatos, testes, pipeline, riscos, desvios e follow-ups; a revisão independente verifica os pontos de maior risco antes da promoção.

## Dependências, links e milestones

Nesta assinatura do GitLab, dependências `blocks/is blocked by` não estão disponíveis. Usamos linked items `relates to`, checklist explícito no issue e `fluxo::bloqueado` para tornar o bloqueio visível. O checklist deve nomear o predecessor, o critério que libera a frente e o artefato esperado. Linked item não substitui child item: child representa decomposição de trabalho; link representa relação entre issues independentes.

As relações centrais são: #77 antes de #31/#32/#33/#35/#48; #47 antes de #32/#33/#48; #41 antes de #48; #42 antes de #32; #58 antes da decisão visual de #65; e #43/#36 antes do fechamento de #34. #31 relaciona-se a #33, sem ser forçada a child. Essas relações documentam gates reais; elas não impedem que as frentes independentes desenvolvam protótipos ou testes em paralelo.

Milestones representam resultados, não cada sessão, horário ou workstream. As três etapas são Fundação e contratos; Exploração, experimentos e seleção de evidências; e Análise validada e narrativa final. O prazo expirado permanece apenas como histórico. Trabalho remoto flexível não deve virar deadline artificial. O milestone final é o lugar para o resultado integrado, não para cada tarefa intermediária. #39 é registro histórico de checkpoints e não é gate.

## Checklist antes de revisão

Execute `uv sync --frozen`, os testes definidos na issue, `uv run python scripts/render_notebooks.py`, `uv run python scripts/render_notebooks.py --check`, `marimo check` e o smoke top-to-bottom. Verifique translation pairs, outputs bounded, manifest, CI e Molab real; HTTP 200 de um preview não prova execução. Registre falhas com pipeline, SHA, job e primeiro trace.

Não feche issue nem marque `Finalizado` apenas porque o código existe. Exija critérios de aceite, CI, artefatos, caveats, handoff e revisão humana. O integrador é o último workstream e só deve incorporar evidência validada ou explicitamente rotulada como protótipo.
