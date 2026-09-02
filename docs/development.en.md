# Marimo development environment

The local environment is the development reference: the repository, `pyproject.toml`, and `uv.lock` define code and dependencies. Molab is the complementary surface for collaboration, demos, and temporary execution; it must not retain a divergent implementation.

## Start locally

```powershell
uv sync --frozen
uv run marimo edit --no-token
```

The first command reproduces locked versions. The second opens the Marimo home page in the browser, where any repository notebook can be opened. The server should listen only on localhost; do not use `--no-token` on an interface exposed to the network.

To start the same shared home/editor for all notebooks in the repository:

```powershell
uv run python scripts/start_marimo.py
```

The command accepts an optional path, for example `uv run python scripts/start_marimo.py notebooks/spotify_analysis.py`.

To open one notebook directly:

```powershell
uv run marimo edit notebooks/spotify_analysis.py --no-token
```

With the notebook open, an agent equipped with the `marimo-pair` skill can discover the local server or receive its URL. Durable changes during an active session should use the kernel code-mode API instead of simultaneous edits to the `.py` file, preventing the kernel from overwriting changes.

## Cloud workflow

After notebooks reach `main`, an “Open in molab” link can open the versioned file directly. Molab is appropriate for presentations, setup-free review, and focused collaboration. Before presenting, execute the cloud notebook from the selected commit and confirm dependencies, CSV access, startup time, and bounded outputs.

Primary development remains local because it provides stable access to the CSV, Git, tests, in-memory DuckDB, and the agent without depending on cloud session limits, quotas, or rate limiting. Changes made in Molab must return as a `.py` file and pass the same tests and merge-request workflow; the cloud notebook is not a second source of truth.

## Validation before sharing

```powershell
uv run python scripts/check_translation_pairs.py
uv run pytest -q
uv run marimo check notebooks/data_contract_audit.py notebooks/spotify_analysis.py notebooks/explorations/popularity_associations.py notebooks/explorations/genre_representations.py notebooks/explorations/musical_structure.py notebooks/explorations/popularity_validation.py
uv run python scripts/smoke_notebooks.py
```

Record the operating system in the merge request when a failure is environment-specific. Never commit `.venv`, Marimo caches, HTML exports, or DuckDB database files.
