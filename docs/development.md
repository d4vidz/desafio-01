# Ambiente de desenvolvimento Marimo

O ambiente local é a referência de desenvolvimento: o repositório, `pyproject.toml` e `uv.lock` definem o código e as dependências. Molab é a superfície complementar para colaboração, demonstração e execução temporária; não deve manter uma implementação divergente.

## Iniciar localmente

```powershell
uv sync --frozen
uv run marimo edit --no-token
```

O primeiro comando reproduz as versões travadas. O segundo abre a home do Marimo no navegador, de onde qualquer notebook do repositório pode ser aberto. O servidor deve escutar apenas em localhost; `--no-token` não deve ser usado em uma interface exposta à rede.

Para iniciar a mesma home/editor compartilhada por todos os notebooks do repositório:

```powershell
uv run python scripts/start_marimo.py
```

O comando aceita um caminho opcional, por exemplo `uv run python scripts/start_marimo.py notebooks/spotify_analysis.py`.

Para abrir diretamente um notebook:

```powershell
uv run marimo edit notebooks/spotify_analysis.py --no-token
```

Com o notebook aberto, um agente equipado com a skill `marimo-pair` pode descobrir o servidor local ou receber sua URL. Alterações duráveis durante uma sessão ativa devem ser feitas pela API de code mode do kernel, não por edição simultânea do arquivo `.py`, evitando que o kernel sobrescreva mudanças.

## Fluxo cloud

Os snapshots HTML locais ficam em `artifacts/notebooks/html/` e são regenerados por `uv run python scripts/render_notebooks.py` a cada commit que altera um notebook. Depois que os notebooks estiverem em `main`, um link “Open in molab” pode abrir diretamente o arquivo versionado. Os links Molab verificados estão em [docs/molab-notebooks.md](molab-notebooks.md). Molab é apropriado para apresentação, revisão sem setup local e colaboração pontual. Antes de apresentar, execute o notebook cloud a partir do commit selecionado e confirme dependências, acesso ao CSV, tempo de inicialização e outputs bounded.

O desenvolvimento principal continua local porque oferece acesso estável ao CSV, Git, testes, DuckDB em memória e ao agente, sem depender de sessão, quota ou rate limiting do serviço cloud. Mudanças feitas no Molab devem voltar como arquivo `.py` e passar pelos mesmos testes/MR; o notebook cloud não é uma segunda fonte de verdade.

### Pin do contexto no Molab

O preview GitHub-backed recebe o arquivo `.py` selecionado, não a árvore inteira
do repositório. Por isso cada notebook contém um bootstrap pequeno que baixa um
arquivo ZIP de um commit imutável. Esse snapshot fornece `spotify_data/` e o CSV;
o hash do CSV é conferido antes da análise. O commit do snapshot deve conter a
camada compartilhada e os dados necessários, mas não precisa ser o mesmo commit
do arquivo de entrada quando apenas a narrativa daquele notebook mudou.

Ao publicar uma alteração em `spotify_data/`, no contrato ou no CSV, atualize
explicitamente todos os pins:

```powershell
uv run python scripts/update_molab_context.py <40-character-commit-sha>
```

Depois regenere os HTMLs, execute os checks e publique o espelho GitHub. O
documento [molab-notebooks.md](molab-notebooks.md) deve registrar o commit e a
data da verificação. Assim a separação dos seis notebooks continua simples sem
permitir que o contexto compartilhado fique silenciosamente desatualizado.

## Validação antes de compartilhar

```powershell
uv run python scripts/check_translation_pairs.py
uv run pytest -q
uv run marimo check notebooks/data_contract_audit.py notebooks/spotify_analysis.py notebooks/explorations/popularity_associations.py notebooks/explorations/genre_representations.py notebooks/explorations/musical_structure.py notebooks/explorations/popularity_validation.py
uv run python scripts/smoke_notebooks.py
```

Registre no merge request o sistema operacional quando uma falha for específica de ambiente. Nunca versione `.venv`, caches Marimo, exports HTML fora de `artifacts/notebooks/html/` ou bancos DuckDB.
