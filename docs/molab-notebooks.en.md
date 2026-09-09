# Molab notebooks

## Publication status

The GitLab repository is canonical. Reviewable HTML snapshots live in
[`artifacts/notebooks/html/`](../artifacts/notebooks/html/). Molab is an
execution and presentation surface, not a second source of truth.

The workspaces created by manual import during diagnosis remain only in the
MR history. They are not the canonical surface: manual import brings the
`.py` file but does not automatically bring `spotify_data/` or `data/raw/`.
The presentation links below use the GitHub-backed preview, which resolves
the notebook and its versioned bootstrap from the public repository.

## GitHub mirror and contextual preview

The public mirror is available at
[`d4vidz/desafio-01`](https://github.com/d4vidz/desafio-01). GitLab remains the
canonical source; GitHub is the public preview and Molab execution surface.
After MR !1 was merged, the links below point to the mirror's `main` branch.
The initial cloud smoke test ran on the branch content at
`35f72904a6e76ee61a5c9b9c28b072e25b59001e`; later commits `6e6887a` and
`ca319a6` changed documentation and the translation manifest only, without
changing the notebooks. They explicitly download the shared context pinned to
`405a0d58b513eaeb8daeac4d2b2b98a65e57a963`; that pin includes the
deterministic sampling helper validated in #77 and is the bootstrap boundary
for the modules/CSV, while notebook code and artifacts are read from the branch.

| Notebook | Contextual Molab preview | Shared runtime | Verification on 2026-09-03 (BRT) |
| --- | --- | --- | --- |
| Data contract audit | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/data_contract_audit.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/data_contract_audit.py/server) | open; cells rendered; no visible error |
| Popularity associations | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_associations.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_associations.py/server) | open; cells rendered; no visible error |
| Genre representations and graphs | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/genre_representations.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/genre_representations.py/server) | open; cells rendered; no visible error |
| Musical structure | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/musical_structure.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/musical_structure.py/server) | open; cells rendered; no visible error |
| Predictive validation and fingerprints | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_validation.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/explorations/popularity_validation.py/server) | open; cells rendered; no visible error |
| Integrating analysis | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/spotify_analysis.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/main/notebooks/spotify_analysis.py/server) | open; scorecard rendered; `Errors: 0` panel |

The HTTP test confirmed that Molab recognizes all six paths and returns each
notebook title. In this revision, “Run it now” was started for every path; a
Luna agent observed the cells, dependencies, CSV access, rendering, and absence
of tracebacks. The integrator's `Errors` panel showed zero. This is a cloud
smoke test of the content promoted to `main`, not a replacement for CI or analytical review: HTTP
200 alone does not prove execution. The preview has a temporary workspace and
does not automatically mount the repository tree. Each notebook bootstrap
downloads the shared pinned context above and checks the CSV hash before
importing the modules.

This flow creates one link per notebook, all pointing to the same repository
and branch; it does not create one file browser that switches notebooks inside
a single URL. A multi-notebook application using
`marimo.create_asgi_app()` would be a custom deployment, not the usual Molab
flow.

Without a mirror, the fallback is to upload the files through the File Browser;
the CSV and modules must be present in the expected tree. A temporary bundle
can be used for this test, but it must not be committed or replace the
versioned CSV.

After a new commit is published to GitLab, update the GitHub mirror before
using the preview. The table must record the source commit/ref, verification
date, all-cell status, CSV access, dependencies, and output size. A link
receives “verified” status only after a top-to-bottom run without errors.

## Local reproduction

```bash
uv run marimo edit notebooks/spotify_analysis.py
uv run python scripts/render_notebooks.py
uv run python scripts/render_notebooks.py --check
```

See also [development.en.md](development.en.md) and
[contributing.en.md](contributing.en.md).

When the shared layer or CSV changes, update all six pins with:

```powershell
uv run python scripts/update_molab_context.py <40-character-commit-sha>
```

The pin is an explicit boundary for shared context, not a second source of
truth or an invitation to edit only the cloud copy.
