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

## Recommended flow

Once the GitHub account is authenticated, the project can be mirrored
one-way (GitLab remains the source) and opened through Molab's GitHub preview.
That flow makes repository files available in the workspace. Without a
mirror, the fallback is to upload the files through the File Browser; the CSV
and modules must be present in the expected tree. A temporary bundle can be
used for this test, but it must not be committed or replace the versioned CSV.

After publication, update this table with permanent links and the source
commit/ref, verification date, all-cell status, CSV access, dependencies, and
output size. A link receives “verified” status only after a top-to-bottom run
without errors.

## Local reproduction

```bash
uv run marimo edit notebooks/spotify_analysis.py
uv run python scripts/render_notebooks.py
uv run python scripts/render_notebooks.py --check
```

See also [development.en.md](development.en.md) and
[contributing.en.md](contributing.en.md).
