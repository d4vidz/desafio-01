# CI: execution and diagnosis

The pipeline runs a frozen environment sync, translation verification, tests, and `marimo check` for the notebooks. A red status alone does not establish that the code failed: first determine whether a job started.

## Minimum merge-request record

1. evaluated SHA and links to branch and merge-request pipelines;
2. status and job list;
3. trace of the first failed job;
4. equivalent local commands and results;
5. classification: creation failure, execution failure, success, or inconclusive.

- `failed` with no jobs: failure before execution; do not attribute it to tests without evidence.
- job with a trace: diagnose the first actionable cause in the log.
- `passed`: verify that it belongs to the current SHA.
- absent, canceled, or skipped pipeline: do not treat it as success.

## Initial MR !1 incident

Pipelines [#2811912477](https://gitlab.com/residencia-em-ia/desafio-01/-/pipelines/2811912477) and [#2811912595](https://gitlab.com/residencia-em-ia/desafio-01/-/pipelines/2811912595), at SHA `fdac0030`, failed before creating any job. The GitLab interface reported: **“Identity verification is required in order to run CI jobs.”** Therefore YAML, dependencies, tests, and notebooks did not fail; those commands never ran on a runner.

To unblock CI, the account that triggers the pipeline must complete GitLab's required verification and create a new pipeline for the current SHA. Until then, run locally:

After verification, pipeline [#2813599791](https://gitlab.com/residencia-em-ia/desafio-01/-/pipelines/2813599791) ran and exposed a real portability failure: the test compared CRLF bytes from the Windows checkout with LF bytes from the Linux runner. The fix adds an LF rule in `.gitattributes` and compares SHA-256 over canonical text content. The versioned CSV and its values were not changed.

```bash
uv sync --frozen
uv run python scripts/check_translation_pairs.py
uv run pytest -q
uv run marimo check notebooks/spotify_analysis.py notebooks/explorations/popularity_baselines.py notebooks/explorations/musical_structure.py
```
