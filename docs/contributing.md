# Fluxo de contribuição

Este projeto é organizado em torno das guide questions do GitLab e de entregas pequenas e revisáveis.

## Antes de codificar

1. Encontre a guide question que motiva o trabalho.
2. Abra ou atualize uma issue focada descrevendo a pergunta, o grain, o método pretendido, o gráfico/tabela/modelo esperado e os caveats conhecidos.
3. Mantenha explorações não relacionadas em uma issue ou notebook separado para que a narrativa final permaneça legível.

Labels históricas (`Descritivas`, `Relacionais` etc.) são preservadas. Para issues novas, use a taxonomia scoped documentada em [docs/governance.md](governance.md): uma label de tipo, uma de fluxo e uma de prioridade, além das labels de evidência e área necessárias. Labels de proveniência `proposta::<origem-ou-rodada>` só devem existir durante uma conferência; depois da decisão, remova-as das issues e aposente-as até uma nova rodada explícita.

Use uma issue de `especificação` antes de implementar contratos compartilhados ou de alto risco, como schema/grain, validação, headline claims, features de grafo e estrutura do notebook final. Uma exploração pequena pode ir diretamente para `entrega`. Toda entrega precisa indicar lead, reviewer, integrador quando aplicável, dependências e definition of done.

## Padrões de notebook e código

- Escreva notebooks Marimo como arquivos Python puros, com células pequenas orientadas por dependências e uma expressão final significativa para cada resultado renderizado.
- Não altere objetos entre células; crie novos frames Polars ou objetos de resultado.
- Reconstrua a camada DuckDB em memória a partir de `data/raw/spotify_tracks.csv` a cada início de runtime.
- Mantenha `tracks_raw`, `tracks_clean`, `tracks`, `track_genres` e `track_artists` distintos e nomeie o grain nas funções de análise e nos títulos dos gráficos. Todo notebook deve consumir a limpeza compartilhada; não replique suas regras em células.
- Prefira Polars tipado a pandas. Mantenha SQL em células ou módulos auxiliares legíveis e testáveis.
- Para a análise humana, use o painel v0.1 em [docs/feature-roles.md](feature-roles.md); mantenha as demais features disponíveis para seleção automatizada e análises de sensibilidade.
- Versione os snapshots HTML produzidos por `scripts/render_notebooks.py` em `artifacts/notebooks/html/` quando um notebook mudar; não versione exports fora dessa pasta, arquivos de banco, caches de notebook ou payloads de gráficos grandes e sem limite.

## Checklist de qualidade dos gráficos

Um gráfico está pronto para revisão quando:

- responde a uma pergunta declarada;
- nomeia a unidade de análise e a agregação;
- usa escala e encoding que não distorcem a comparação;
- trata explicitamente grupos esparsos, duplicatas e faixas com múltiplos gêneros;
- inclui uma interpretação concisa e uma limitação;
- é renderizado como output bounded no Marimo.

Treemaps exigem uma hierarquia significativa e uma medida de tamanho aditiva. Redes exigem nós, arestas, agregação e um controle de top-*n* ou filtro definidos. Uma lista decorativa de categorias não é uma hierarquia ou grafo válido.

## Validação e merge requests

Use branches curtas e merge requests conforme [docs/branching.md](branching.md). Não faça push direto em `main`. Referencie issues com `Refs #IID`; use palavras-chave de fechamento apenas quando a definition of done estiver integralmente satisfeita.

Execute os checks relevantes antes de abrir um merge request:

```bash
uv sync
uv run marimo check notebooks/spotify_analysis.py
uv run marimo check notebooks/explorations/musical_structure.py
uv run python scripts/render_notebooks.py
uv run python scripts/render_notebooks.py --check
uv run pytest
```

O merge request deve resumir a pergunta respondida, o grain dos dados, os outputs alterados, os comandos de validação e a incerteza restante. Deve vincular a issue do GitLab e declarar se o trabalho pertence a Fundação e contratos, Exploração/experimentos e seleção de evidências ou Análise validada/narrativa final. Feche a issue somente quando o código for reproduzível, o output tiver sido revisado e a definition of done documentada estiver satisfeita.

O guia de governança em português está em [docs/governance.md](governance.md); a tradução em inglês está em [docs/governance.en.md](governance.en.md).
Para configurar o ambiente e escolher entre execução local e Molab, consulte [docs/development.md](development.md). Para diagnosticar pipelines, consulte [docs/ci.md](ci.md).
