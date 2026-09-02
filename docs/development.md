# Ambiente de desenvolvimento Marimo

O ambiente local é a referência de desenvolvimento: o repositório, `pyproject.toml` e `uv.lock` definem o código e as dependências. Molab é a superfície complementar para colaboração, demonstração e execução temporária; não deve manter uma implementação divergente.

## Iniciar localmente

```powershell
uv sync --frozen
uv run marimo edit --no-token
```

O primeiro comando reproduz as versões travadas. O segundo abre a home do Marimo no navegador, de onde qualquer notebook do repositório pode ser aberto. O servidor deve escutar apenas em localhost; `--no-token` não deve ser usado em uma interface exposta à rede.

Para abrir diretamente um notebook:

```powershell
uv run marimo edit notebooks/spotify_analysis.py --no-token
```

Com o notebook aberto, um agente equipado com a skill `marimo-pair` pode descobrir o servidor local ou receber sua URL. Alterações duráveis durante uma sessão ativa devem ser feitas pela API de code mode do kernel, não por edição simultânea do arquivo `.py`, evitando que o kernel sobrescreva mudanças.

## Fluxo cloud

Depois que os notebooks estiverem em `main`, um link “Open in molab” pode abrir diretamente o arquivo versionado. Molab é apropriado para apresentação, revisão sem setup local e colaboração pontual. Antes de apresentar, execute o notebook cloud a partir do commit selecionado e confirme dependências, acesso ao CSV, tempo de inicialização e outputs bounded.

O desenvolvimento principal continua local porque oferece acesso estável ao CSV, Git, testes, DuckDB em memória e ao agente, sem depender de sessão, quota ou rate limiting do serviço cloud. Mudanças feitas no Molab devem voltar como arquivo `.py` e passar pelos mesmos testes/MR; o notebook cloud não é uma segunda fonte de verdade.

## Validação antes de compartilhar

```powershell
uv run python scripts/check_translation_pairs.py
uv run pytest -q
uv run marimo check notebooks/spotify_analysis.py notebooks/explorations/popularity_baselines.py notebooks/explorations/musical_structure.py
```

Registre no merge request o sistema operacional quando uma falha for específica de ambiente. Nunca versione `.venv`, caches Marimo, exports HTML ou bancos DuckDB.
