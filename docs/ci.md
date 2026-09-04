# CI: execução e diagnóstico

O pipeline executa sincronização congelada do ambiente, verificação das traduções, testes e `marimo check` dos notebooks. Um status vermelho não basta para concluir que o código falhou: primeiro identifique se algum job chegou a iniciar.

## Registro mínimo por merge request

1. SHA avaliado e links dos pipelines de branch e merge request;
2. status e lista de jobs;
3. trace do primeiro job que falhou;
4. comandos locais equivalentes e resultado;
5. classificação: falha de criação, falha de execução, sucesso ou inconclusivo.

- `failed` sem jobs: falha anterior à execução; não atribuir a testes sem evidência.
- job com trace: diagnosticar a primeira causa acionável no log.
- `passed`: conferir se corresponde ao SHA atual.
- pipeline ausente, cancelado ou skipped: não tratar como sucesso.

## Incidente inicial do MR !1

Os pipelines [#2811912477](https://gitlab.com/residencia-em-ia/desafio-01/-/pipelines/2811912477) e [#2811912595](https://gitlab.com/residencia-em-ia/desafio-01/-/pipelines/2811912595), no SHA `fdac0030`, falharam antes de criar qualquer job. A interface do GitLab informou: **“Identity verification is required in order to run CI jobs”**. Portanto, não houve falha de YAML, dependência, teste ou notebook; esses comandos não chegaram a executar no runner.

Para destravar o CI, a conta que dispara o pipeline deve concluir a verificação exigida pelo GitLab e criar um novo pipeline para o SHA atual. Enquanto isso, execute localmente:

Depois da verificação, o pipeline [#2813599791](https://gitlab.com/residencia-em-ia/desafio-01/-/pipelines/2813599791) executou e expôs uma falha real de portabilidade: o teste comparava bytes CRLF do checkout Windows com bytes LF do runner Linux. A correção adiciona uma regra LF em `.gitattributes` e compara o SHA-256 do conteúdo textual canônico. O CSV versionado e seus valores não foram alterados.

No pipeline [#2818744127](https://gitlab.com/residencia-em-ia/desafio-01/-/pipelines/2818744127), do commit `ac124c50`, o job `governance` iniciou e falhou em `tests/test_notebook_artifacts.py::test_committed_manifest_matches_current_sources_and_html`. O trace mostra que tradução e instalação passaram; a divergência reapareceu porque `scripts/render_notebooks.py` gerava o hash do notebook a partir dos bytes locais, enquanto o runner Linux calculava o hash a partir de LF. Portanto, a causa era a proveniência dos snapshots, não o CSV, o ambiente ou a execução do Marimo. O commit `120d00c` normaliza CRLF/LF em `source_digest()` e adiciona um teste de regressão; localmente a suíte passou de 30 para 31 testes aprovados.

```bash
uv sync --frozen
uv run python scripts/check_translation_pairs.py
uv run pytest -q
uv run marimo check notebooks/data_contract_audit.py notebooks/spotify_analysis.py notebooks/explorations/popularity_associations.py notebooks/explorations/genre_representations.py notebooks/explorations/musical_structure.py notebooks/explorations/popularity_validation.py
```
