# Contrato de dados

A versão canônica deste documento é esta. A tradução em inglês está em
[`data-contract.en.md`](data-contract.en.md); mantenha os dois arquivos
sincronizados quando o contrato mudar.

Este contrato mantém a análise do Spotify reproduzível e evita a mistura
acidental de grãos de linha.

## Fonte

A fonte esperada é `data/raw/spotify_tracks.csv`. Ela é a entrada
autoritativa de cada execução e deve ser preservada sem alterações. O primeiro
campo do CSV tem cabeçalho vazio e é exposto como `source_row_id`,
exclusivamente para auditoria da linha de origem. O carregador tipado declara o
schema restante em `spotify_data/data_contract.py`; não depende de
autodetecção.

Campos vazios do CSV tornam-se nulos. Nenhum valor é preenchido.
`load_tracks_raw` valida nomes, ordem e tipos antes de qualquer transformação.

O projeto não persiste um banco analítico. Em runtime, crie
`duckdb.connect(":memory:")`, carregue o CSV em tabelas temporárias ou
restritas à sessão e reconstrua essas tabelas após cada reinício. Arquivos
`.duckdb`, `.db` ou bancos materializados persistentes estão fora do escopo.

## Grãos

| Relação | Grão | Uso |
| --- | --- | --- |
| `tracks_raw` | uma linha da fonte | auditar duplicatas, nulos, valores inválidos e fidelidade da fonte |
| `tracks_clean` | uma linha limpa da fonte, sem o índice exportado | entrada comum para todas as relações analíticas |
| `tracks` | uma linha por `track_id` | distribuições por faixa, PCA, clustering e popularidade |
| `track_genres` | uma linha por `track_id` × gênero | comparações, sobreposição e visões derivadas de grafos |
| `track_artists` | uma linha por `track_id` × artista | rede artista–gênero e agregações |

A fonte pode conter valores repetidos de `track_id` porque uma faixa pode
aparecer em mais de uma relação com gênero. Nunca trate silenciosamente as
linhas da fonte como faixas independentes. Identificadores nulos são
reportados; relações filhas que dependem deles excluem essas linhas sem
inventar chaves.

`tracks_clean` reproduz a limpeza auditada no notebook [Spotify Data
Cleaning](https://molab.marimo.io/notebooks/nb_FP1VJkrCoXJwRVExDxZibv):
remove a única linha com `artists`, `album_name` e `track_name` ausentes,
descarta `source_row_id` da relação analítica, remove 450 cópias exatamente
duplicadas desconsiderando esse índice e apara espaços externos de `artists`
e `track_name`. A fonte permanece intacta em `tracks_raw`. O resultado tem
113.549 linhas e 20 colunas. Não persista um segundo CSV limpo; todos os
notebooks devem reconstruir esta relação pelo mesmo módulo.

Para cada `track_id`, `tracks` usa a mediana da popularidade e preserva
`popularity_min`, `popularity_max`, `popularity_count`,
`popularity_distinct_count`, `popularity_range` e `popularity_conflict`.
Assim, a deduplicação fica observável em vez de silenciosa. Outros campos
repetidos de metadados e audio features são reduzidos com `MIN` determinístico
somente após uma validação fail-fast: qualquer divergência, inclusive entre
nulo e não nulo, interrompe a construção. Popularidade e gênero são exceções;
gênero é explicitamente many-to-many. O gênero em `tracks` é apenas um valor
representativo; a análise por gênero usa `track_genres`.

A separação de artistas usa somente o literal `;`. Vírgulas, barras, `&` e
outras pontuações permanecem no rótulo do artista. Espaços são removidos nas
extremidades, os rótulos são normalizados com Unicode NFKC, componentes vazios
são descartados e o primeiro `artist_position` observado é preservado. A
relação final é distinta por `track_id` × artista.

## Checks de qualidade

No mínimo, reporte:

- contagem e percentual de missingness por coluna;
- linhas exatamente duplicadas e contagem de `track_id` repetidos;
- intervalos numéricos esperados e candidatos a sentinel, incluindo durações ou tempos iguais a zero;
- valores numéricos não finitos e falhas de parsing;
- mudanças de cardinalidade de `tracks_raw` para `tracks_clean`, `tracks` e `track_genres`;
- gêneros esparsos e quantidade de relações com múltiplos gêneros.

Não há imputation na fonte nem nas tabelas canônicas. `tracks_raw` preserva
nulos; uma análise pode excluir linhas quando um identificador for necessário,
mas não deve inventar valores de features. A fonte atual não tem missingness
numérica, portanto um experimento artificial de imputation está fora do
escopo. Se uma fonte futura tiver nulos numéricos, imputation deverá ser uma
decisão analítica separada, com indicador de missingness e análise de
sensibilidade, nunca uma sobrescrita de `tracks_raw`.

## Fronteiras tipadas

Use Polars (`pl.DataFrame`/`pl.LazyFrame`) para ingestão tipada explícita, o
parser conservador de artistas, matrizes de features e entradas bounded para
gráficos. Use DuckDB SQL para tabelas relacionais temporárias, deduplicação,
joins e agregações. Converta resultados SQL para Polars na fronteira e
mantenha as entradas dos gráficos pequenas o suficiente para renderização
interativa no Marimo.

## Limites de interpretação

Cada runtime cria explicitamente `duckdb.connect(":memory:")` e reconstrói as
tabelas temporárias a partir do CSV. Nenhum arquivo `.duckdb` é persistido.
Popularidade é uma variável observada do catálogo, não um resultado causal nem
uma medida direta de ouvintes. PCA e clustering resumem a geometria das
features; não revelam segmentos de ouvintes. Comparações por gênero devem
declarar a regra de contagem de múltiplos gêneros e evitar a superinterpretação
de categorias esparsas. Claims preditivos exigem target declarado, revisão de
leakage, divisão por grupo/tempo quando apropriado e métricas held-out.
