## Resumo

Descreva a pergunta, especificação e entrega cobertas por este merge request.

## Referências GitLab

- Pergunta(s):
- Especificação(ões):
- Issue(s) de entrega:
  <!-- Use Closes #IID somente quando a definição de pronto estiver satisfeita. -->
- Milestone:

## Escopo analítico

- Fonte e versão/hash:
- Grain e população:
- Filtros, agregações e top-*n*:
- Regras de missingness, duplicatas e outliers:

## Implementação

Descreva as mudanças em DuckDB, Polars, Marimo, modelagem, visualização ou documentação. Registre qualquer desvio de uma especificação.

## Evidência e interpretação

- Resultados principais:
- Visualizações/tabelas alteradas:
- Claim que pode ser feito:
- Claim que não pode ser feito:
- Incerteza, caveats e resultado inconclusivo:

## Validação executada

```text
uv run pytest
uv run marimo check notebooks/spotify_analysis.py
uv run python notebooks/spotify_analysis.py
```

Acrescente comandos específicos, fixtures, métricas e resultados relevantes.

## Checklist

- [ ] A pergunta e a especificação relacionadas estão vinculadas.
- [ ] O resultado é reproduzível a partir da fonte versionada.
- [ ] O grain, as agregações e a unidade de cada visual estão claros.
- [ ] Outputs do Marimo, gráficos, tabelas e exports estão bounded.
- [ ] Interações/defaults foram testados quando aplicável.
- [ ] Claims não excedem a evidência; caveats estão registrados.
- [ ] Documentação em português foi atualizada e a tradução correspondente foi sincronizada.
- [ ] Mudanças de escopo têm registro e aprovação.
