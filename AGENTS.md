# Instruções para agentes

Estas instruções valem para qualquer agente que trabalhe neste repositório.

## Antes de editar

1. Leia a issue/Task, a especificação relacionada e [o contrato de comunicação](docs/notebook-communication.md).
2. Confirme o grain, a população, o status da evidência e o limite do claim.
3. Preserve a camada compartilhada de dados; não replique limpeza, schema ou construção DuckDB dentro do notebook.
4. Declare o que está fora do escopo e os testes exigidos antes de implementar.

## Ao criar ou alterar um notebook

- A documentação nasce na mesma alteração que cria a análise ou visualização.
- Toda visualização principal deve explicar pergunta, população, unidade, método intuitivo, leitura, denominador/amostra, resultado dinâmico e limitação.
- Use o renderer e os tipos de `spotify_data.notebook_ui` quando disponíveis.
- Informação essencial deve aparecer no fluxo principal e no HTML estático; não dependa de hover, tooltip ou accordion.
- Marque explicitamente `infraestrutura`, `protótipo`, `experimento_completo` ou `evidência_validada`.
- Não transforme associação em causalidade nem protótipo em claim.

## Antes de entregar

- Atualize HTML e manifest quando o notebook mudar.
- Execute os checks definidos na issue e registre comando, resultado e ambiente.
- Entregue o índice Luna → Sol: issues, commits, arquivos/seções, artefatos, testes, riscos, desvios e follow-ups.
- Não feche issue nem resolva discussão de MR sem critério de aceite e revisão humana.

Leia a skill [spotify-marimo-notebook](.agents/skills/spotify-marimo-notebook/SKILL.md) para o procedimento completo. Os contratos detalhados estão em `docs/notebook-communication.md` e `docs/agent-review.md`.
