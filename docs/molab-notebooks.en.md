# Molab notebooks

## Publication status

The GitLab repository is canonical. Reviewable HTML snapshots live in
[`artifacts/notebooks/html/`](../artifacts/notebooks/html/). Molab is an
execution and presentation surface, not a second source of truth.

In this revision, all six files were imported individually to test the flow,
but these copies are not presentation-ready links yet: a manual import brings
the `.py` file but does not automatically bring `spotify_data/` or
`data/raw/`. The links below are diagnostic only until repository context is
available in the workspace:

| Notebook | Provisional link | Status |
| --- | --- | --- |
| Data contract audit | [Molab](https://molab.marimo.io/notebooks/nb_nm24Z1e5m9uJxZ2yUB6AZ9) | imported; context missing |
| Popularity associations | [Molab](https://molab.marimo.io/notebooks/nb_zE8LLWPkJhUMXfHuT1XAf8) | imported; context missing |
| Genre representations and graphs | [Molab](https://molab.marimo.io/notebooks/nb_wTkiw2tCkVJ6pryCLXE7rC) | imported; context missing |
| Musical structure | [Molab](https://molab.marimo.io/notebooks/nb_FnmjDFh6mu7NdK4AhA8mbv) | imported; context missing |
| Predictive validation and fingerprints | [Molab](https://molab.marimo.io/notebooks/nb_NG4NB8MfPymmLy4bxoEq3N) | imported; context missing |
| Integrating analysis | [Molab](https://molab.marimo.io/notebooks/nb_KHYNaR7cz9CKmiRaGfDVZt) | imported; context missing |

## GitHub mirror and contextual preview

The public mirror is available at
[`d4vidz/desafio-01`](https://github.com/d4vidz/desafio-01). GitLab remains the
canonical source; GitHub is the public preview and Molab execution surface.
The branch below contains the current working commit
`35f72904a6e76ee61a5c9b9c28b072e25b59001e`. The notebooks still download the
shared context explicitly pinned to
`12f6f86d857b55ddd37ab0b1a575dfb49b7f3f36`; that pin is the bootstrap boundary
for the modules/CSV, while notebook code and artifacts are read from the branch.

| Notebook | Contextual Molab preview | Shared runtime | Verification on 2026-09-03 (BRT) |
| --- | --- | --- | --- |
| Data contract audit | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/data_contract_audit.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/data_contract_audit.py/server) | open; cells rendered; no visible error |
| Popularity associations | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/popularity_associations.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/popularity_associations.py/server) | open; cells rendered; no visible error |
| Genre representations and graphs | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/genre_representations.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/genre_representations.py/server) | open; cells rendered; no visible error |
| Musical structure | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/musical_structure.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/musical_structure.py/server) | open; cells rendered; no visible error |
| Predictive validation and fingerprints | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/popularity_validation.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/explorations/popularity_validation.py/server) | open; cells rendered; no visible error |
| Integrating analysis | [open](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/spotify_analysis.py) | [open runtime](https://molab.marimo.io/github/d4vidz/desafio-01/blob/chore/45-versionar-governanca-e-analises/notebooks/spotify_analysis.py/server) | open; scorecard rendered; `Errors: 0` panel |

The HTTP test confirmed that Molab recognizes all six paths and returns each
notebook title. In this revision, “Run it now” was started for every path; a
Luna agent observed the cells, dependencies, CSV access, rendering, and absence
of tracebacks. The integrator's `Errors` panel showed zero. This is a cloud
smoke test of the branch, not a replacement for CI or analytical review: HTTP
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
