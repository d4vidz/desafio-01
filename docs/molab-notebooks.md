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

## Fluxo recomendado

Quando a conta GitHub estiver autenticada, o projeto pode ser espelhado de
forma unidirecional (GitLab continua sendo a origem) e aberto pelo preview
GitHub do Molab. Esse fluxo disponibiliza os arquivos do repositório no
workspace. Para um repositório GitLab sem mirror, o fallback é fazer upload
dos arquivos pelo File Browser; o CSV e os módulos precisam estar na árvore
esperada. Um bundle temporário pode ser usado para esse teste, mas não deve
ser commitado nem substituir o CSV versionado.

Após a publicação, esta tabela deve ser atualizada com os links permanentes e
com: commit/ref de origem, data de verificação, status de todas as células,
acesso ao CSV, dependências e tamanho dos outputs. Um link só recebe o status
“verificado” depois de uma execução top-to-bottom sem erro.

## Reprodução local

```bash
uv run marimo edit notebooks/spotify_analysis.py
uv run python scripts/render_notebooks.py
uv run python scripts/render_notebooks.py --check
```

Consulte também [development.md](development.md) e
[contributing.md](contributing.md).
