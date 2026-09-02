# Notebooks no Molab

## Estado da publicação

O desenvolvimento canônico é o repositório GitLab. Os HTML revisáveis ficam
em [`artifacts/notebooks/html/`](../artifacts/notebooks/html/). O Molab é uma
superfície de execução e apresentação; não é uma segunda fonte de verdade.

Nesta revisão, os seis arquivos foram importados individualmente para testar o
fluxo, mas essas cópias ainda não são links de apresentação validados: uma
importação manual traz o `.py`, porém não traz automaticamente
`spotify_data/` nem `data/raw/`. Os links abaixo são mantidos apenas para
diagnóstico até que o contexto do repositório seja disponibilizado no
workspace:

| Notebook | Link provisório | Situação |
| --- | --- | --- |
| Auditoria do contrato | [Molab](https://molab.marimo.io/notebooks/nb_nm24Z1e5m9uJxZ2yUB6AZ9) | importado; falta contexto |
| Associações de popularidade | [Molab](https://molab.marimo.io/notebooks/nb_zE8LLWPkJhUMXfHuT1XAf8) | importado; falta contexto |
| Representações de gênero e grafos | [Molab](https://molab.marimo.io/notebooks/nb_wTkiw2tCkVJ6pryCLXE7rC) | importado; falta contexto |
| Estrutura musical | [Molab](https://molab.marimo.io/notebooks/nb_FnmjDFh6mu7NdK4AhA8mbv) | importado; falta contexto |
| Validação preditiva e fingerprints | [Molab](https://molab.marimo.io/notebooks/nb_NG4NB8MfPymmLy4bxoEq3N) | importado; falta contexto |
| Análise integradora | [Molab](https://molab.marimo.io/notebooks/nb_KHYNaR7cz9CKmiRaGfDVZt) | importado; falta contexto |

## Espelho GitHub e preview contextual

O espelho público foi criado em
[`d4vidz/desafio-01`](https://github.com/d4vidz/desafio-01). O GitLab continua
sendo a origem canônica; o GitHub serve como superfície pública de preview e
execução no Molab. O branch abaixo contém o commit de trabalho atual
`2ee61b4`:

| Notebook | Preview contextual no Molab | Verificação em 02/09/2026 (BRT) |
| --- | --- | --- |
| Auditoria do contrato | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/data_contract_audit.py) | rota HTTP 200; runtime pendente |
| Associações de popularidade | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/popularity_associations.py) | rota HTTP 200; runtime pendente |
| Representações de gênero e grafos | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/genre_representations.py) | rota HTTP 200; runtime pendente |
| Estrutura musical | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/musical_structure.py) | rota HTTP 200; runtime pendente |
| Validação preditiva e fingerprints | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/popularity_validation.py) | rota HTTP 200; runtime pendente |
| Análise integradora | [abrir](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/spotify_analysis.py) | rota HTTP 200; runtime pendente |

O teste HTTP confirmou que o Molab reconhece os seis caminhos e retorna o
título do notebook. A execução interativa ainda não foi marcada como
verificada: o navegador recebeu `ERR_CONNECTION_RESET` ao iniciar essas rotas.
Isso é diferente do erro anterior de contexto ausente na importação manual e
deve ser retestado quando o serviço aceitar a sessão.

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
