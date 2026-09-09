# Notebooks no Molab

## Estado da publicação

O desenvolvimento canônico é o repositório GitLab. Os HTML revisáveis ficam
em [`artifacts/notebooks/html/`](../artifacts/notebooks/html/). O Molab é uma
superfície de execução e apresentação; não é uma segunda fonte de verdade.

Os workspaces criados por importação manual durante o diagnóstico ficam
registrados apenas no histórico do MR. Eles não são a superfície canônica:
uma importação manual traz o `.py`, porém não traz automaticamente
`spotify_data/` nem `data/raw/`. Os links de apresentação abaixo usam o
preview GitHub-backed, que resolve o notebook e seu bootstrap versionado a
partir do repositório público.

## Espelho GitHub e preview contextual

O espelho público foi criado em
[`d4vidz/desafio-01`](https://github.com/d4vidz/desafio-01). O GitLab continua
sendo a origem canônica; o GitHub serve como superfície pública de preview e
execução no Molab. Depois do merge do MR !1, os links abaixo apontam para a
`main` do espelho GitHub. O smoke test cloud inicial foi executado no conteúdo
do branch em `35f72904a6e76ee61a5c9b9c28b072e25b59001e`; os commits posteriores
`6e6887a` e `ca319a6` alteraram somente documentação e o manifesto de
tradução, sem alterar os notebooks. Eles baixam, de forma explícita, o
contexto compartilhado pinado em
`405a0d58b513eaeb8daeac4d2b2b98a65e57a963`; esse pin inclui o helper de
amostragem determinística validado na #77 e é a fronteira dos
módulos/CSV usados pelo bootstrap, enquanto o código do notebook e os
artefatos são lidos do branch.

| Notebook | Preview contextual no Molab | Runtime compartilhado | Verificação em 03/09/2026 (BRT) |
| --- | --- | --- | --- |
| Auditoria do contrato | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/data_contract_audit.py) | [abrir runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/data_contract_audit.py/server) | aberto; células renderizadas; nenhum erro visível |
| Associações de popularidade | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_associations.py) | [abrir runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_associations.py/server) | aberto; células renderizadas; nenhum erro visível |
| Representações de gênero e grafos | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/genre_representations.py) | [abrir runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/genre_representations.py/server) | aberto; células renderizadas; nenhum erro visível |
| Estrutura musical | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/musical_structure.py) | [abrir runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/musical_structure.py/server) | aberto; células renderizadas; nenhum erro visível |
| Validação preditiva e fingerprints | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_validation.py) | [abrir runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_validation.py/server) | aberto; células renderizadas; nenhum erro visível |
| Análise integradora | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/spotify_analysis.py) | [abrir runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/spotify_analysis.py/server) | aberto; scorecard renderizado; painel `Errors: 0` |

O teste HTTP confirmou que o Molab reconhece os seis caminhos e retorna o
título do notebook. Nesta revisão, o runtime foi iniciado com “Run it now” para
cada caminho; um agente Luna observou as células, dependências, acesso ao CSV,
renderização e ausência de traceback. No integrador, o painel `Errors` exibiu
zero. Isso é um smoke test cloud do conteúdo promovido para `main`, não
substitui CI nem a revisão analítica: HTTP 200 isolado não prova execução. O
preview tem um workspace
temporário e não monta automaticamente a árvore do repositório. O bootstrap de
cada notebook baixa o contexto compartilhado pinado acima e verifica o hash do
CSV antes de importar os módulos.

Esse fluxo cria um link por notebook, todos apontando para o mesmo repositório
e branch, mas não um único explorador de arquivos que alterne notebooks dentro
de uma mesma URL. Uma aplicação multi-notebook com `marimo.create_asgi_app()`
seria uma implantação própria, não o fluxo usual do Molab.

Para um repositório GitLab sem mirror, o fallback é fazer upload dos arquivos
pelo File Browser; o CSV e os módulos precisam estar na árvore esperada. Um
bundle temporário pode ser usado para esse teste, mas não deve ser commitado
nem substituir o CSV versionado.

Após a publicação de um novo commit no GitLab, atualize o espelho GitHub antes
de usar o preview. A tabela deve registrar commit/ref de origem, data de
verificação, status de todas as células, acesso ao CSV, dependências e tamanho
dos outputs. Um link só recebe o status “verificado” depois de uma execução
top-to-bottom sem erro.

## Reprodução local

```bash
uv run marimo edit notebooks/spotify_analysis.py
uv run python scripts/render_notebooks.py
uv run python scripts/render_notebooks.py --check
```

Consulte também [development.md](development.md) e
[contributing.md](contributing.md).

Quando a camada compartilhada ou o CSV mudar, atualize os seis pins com:

```powershell
uv run python scripts/update_molab_context.py <40-character-commit-sha>
```

O pin é uma fronteira explícita do contexto compartilhado; não é uma segunda
fonte de verdade nem um convite para editar somente a cópia cloud.
