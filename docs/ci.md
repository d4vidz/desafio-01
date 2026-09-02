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

```bash
uv sync --frozen
uv run python scripts/check_translation_pairs.py
uv run pytest -q
uv run marimo check notebooks/spotify_analysis.py notebooks/explorations/popularity_baselines.py notebooks/explorations/musical_structure.py
```
