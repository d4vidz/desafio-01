# Análise de faixas do Spotify

Análise exploratória reproduzível de metadados e audio features de faixas do Spotify usando [Marimo](https://marimo.io/), [DuckDB](https://duckdb.org/) e [Polars](https://pola.rs/).

O projeto é orientado por perguntas: gráficos e modelos devem responder a uma pergunta documentada, tornar explícitos seu grain e sua agregação e declarar o que os dados não permitem estabelecer. A primeira etapa cobre qualidade e missingness dos dados, distribuições, relações, comparações por gênero musical, PCA, clustering, visões derivadas de grafos e modelagem preditiva validada. Como as features numéricas não têm missing values, esta versão documenta a decisão de não imputar.

## Estrutura do repositório

```text
data/raw/spotify_tracks.csv       # CSV de entrada
docs/data-contract.md             # fonte, grain, schema e regras de qualidade
docs/feature-roles.md             # papéis v0.1 das features e protocolo de evidência
docs/contributing.md              # fluxo de issues, gráficos e merge requests
docs/branching.md                 # branches, commits, revisão e proteção de main
docs/development.md               # ambiente local, Molab e pareamento com agentes
docs/ci.md                        # diagnóstico e registro de pipelines
docs/team-next-steps.md           # ponto de partida e handoff do time
notebooks/                        # notebooks Marimo (.py)
tests/                            # testes focados
pyproject.toml                   # dependências e ferramentas do projeto
```

## Início rápido

Requer Python 3.12+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run marimo edit notebooks/spotify_analysis.py
```

Para uma execução smoke não interativa e validação do notebook:

```bash
uv run marimo check notebooks/spotify_analysis.py
uv run marimo export html notebooks/spotify_analysis.py -o spotify_analysis.html --no-include-code
uv run pytest
```

O arquivo de entrada deve estar em `data/raw/spotify_tracks.csv`. O notebook deve falhar com uma mensagem clara se o arquivo não estiver presente; não baixe, sintetize ou substitua a fonte silenciosamente.

## Arquitetura de dados

Cada runtime cria uma conexão DuckDB em memória e reconstrói suas tabelas a partir do CSV bruto. DuckDB é uma camada efêmera de consulta: não crie, versiona, faça cache nem dependa de arquivos `.duckdb`/`.db`. Use DuckDB para scans, joins, deduplicação, window functions e SQL agrupado; retorne resultados bounded para o trabalho tipado de features e gráficos em Polars.

A análise usa relações com quatro grains explícitos:

- `tracks_raw`: uma linha por linha do CSV de origem; duplicatas são mantidas para auditoria.
- `tracks_clean`: uma linha limpa da fonte, sem o índice exportado, usada como entrada compartilhada.
- `tracks`: uma linha canônica por `track_id`, usada para features por faixa, PCA, clustering e resumos de popularidade.
- `track_genres`: uma linha por relação faixa–gênero, usada para comparações por gênero e visões derivadas de grafos.

Consulte [docs/data-contract.md](docs/data-contract.md) para o contrato completo e a política de qualidade.
A justificativa medida para a camada efêmera de DuckDB está em [docs/duckdb-benchmark.md](docs/duckdb-benchmark.md).

## Princípios de visualização

Todo gráfico deve identificar sua pergunta, unidade de análise, agregação e caveat relevante. Outputs devem ser bounded e legíveis no Marimo; evite exibir tabelas completas ou objetos de grafo brutos. Gráficos por gênero devem mostrar o tratamento de grupos esparsos e esclarecer se faixas com múltiplos gêneros contribuem para vários grupos. Treemaps e redes só são permitidos quando a hierarquia ou as arestas representam uma relação significativa, por exemplo, `genre → artist → track` ou uma rede agregada de sobreposição entre gêneros.

## Contribuição

Comece pelas guide questions existentes no GitLab e abra uma issue focada para a análise ou entrega de engenharia concreta. Vincule a issue à pergunta, ao grain, ao método, ao artifact esperado, aos caveats e à definition of done. Mantenha claims exploratórios descritivos, salvo quando um target validado e uma avaliação held-out sustentarem um claim preditivo. O fluxo completo está em [docs/contributing.md](docs/contributing.md).

As convenções de Git estão em [docs/branching.md](docs/branching.md).
O ambiente e o uso local/Molab estão em [docs/development.md](docs/development.md); o handoff operacional do time está em [docs/team-next-steps.md](docs/team-next-steps.md).

## Escopo atual e próximos caminhos

Os milestones iniciais são Fundação e contratos, Exploração/experimentos e seleção de evidências e Análise validada/narrativa final. Possíveis follow-ups incluem grafos de sobreposição entre gêneros e de artista–gênero, análise de sensibilidade para políticas de duplicatas e múltiplos gêneros, análise orientada por tempo se dados temporais forem adicionados e modelagem baseline de popularidade com avaliação group-aware. São hipóteses a investigar, não conclusões implícitas no CSV atual.
