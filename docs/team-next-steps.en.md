# Team next steps

## Starting point and gate

The common starting point is `main` containing gate #77 (deterministic ordering and sampling). Each workstream starts from that `main`, uses its own issue-linked branch, and opens an MR, preferably Draft at first. The MR sequence is:

`associations → genres → clustering → prediction → integration`.

Do not promote numbers, rankings, or claims derived before #77. Planned branches/worktrees are:

- `analysis/33-popularity-associations`: #31/#33 and association Tasks;
- `experiment/32-genre-structure`: #32 and genre representations, profiles, and graphs;
- `experiment/35-clustering-gate`: #35 and PCA, loadings, clustering, stability, and null reference;
- `model/48-popularity-validation`: #41/#48 and predictive validation, splits, and fingerprints;
- `experiment/58-widget-utility`: widget laboratory;
- `integrate/34-final-story`: final integration, exports, and Molab.

No parallel workstream edits `notebooks/spotify_analysis.py`; that file belongs exclusively to the integrator. Each branch must be rebased onto `main` before merge, with deterministic tests and HTML/manifest regeneration.

## Notebook organization

Use the shared data layer and do not replicate cleaning, schema, or DuckDB in experiment cells. The contract/audit notebook documents source, grain, counts, ranges, duplicates, conflicts, and missingness policy. Workstream notebooks consume that layer and repeat the evidence capsule without hiding the population's origin.

Canonical notebooks are:

- `notebooks/data_contract_audit.py`: contract and quality;
- `notebooks/explorations/popularity_associations.py`: statistical associations and #31/#33 EDA;
- `notebooks/explorations/genre_representations.py`: multi-hot, PPMI/SVD, genre profiles, and graphs;
- `notebooks/explorations/musical_structure.py`: PCA, loadings, K-means/GMM, and stability;
- `notebooks/explorations/popularity_validation.py`: baselines, group-aware splits, MAE, and fingerprints;
- `notebooks/spotify_analysis.py`: reviewed evidence and promoted results only.

The #58 laboratory and `experiment/46-rapid-triage` are non-integrable Draft MRs/labs. They test utility and record decisions; only a validated verdict is ported to a workstream or the integrator. #81 (NMF/concept probes) and #78 (neural challengers/concept bottleneck) are second-wave work and do not block the critical path.

## Work contracts

Every delivery must declare issue/spec, fixed point, branch, authorized files, non-goals, population, grain, evidence status, claim ceiling, acceptance criteria, and tests. Communication is created with the code: every main visualization states its question, population/filters, unit, intuitive method, how to read it, denominator or top-*n*, result of this run, interpretation, use, and limit.

The predictive notebook is the canonical producer of `artifacts/evaluation/popularity_validation.json`, splits, metrics, intervals, and promoted models. The integrator loads that artifact by default and, after explicit user action, refits only promoted models; it never silently replaces the official artifact. Claims must distinguish association, contemporary held-out prediction, and causality.

Every notebook change updates HTML and `artifacts/notebooks/manifest.json`. The Luna handoff must contain an addressable index of issues, commits, paths/sections, artifacts, tests, pipeline, risks, deviations, and follow-ups. Sol is required only for high-risk changes under #68/#36 and audits specification, code, analytical validity, and communication; merge remains a human decision.

## Dependencies, links, and flow

In this GitLab tier, `blocks/is blocked by` dependencies are unavailable. We use `relates to` linked items, an explicit issue checklist, and `fluxo::bloqueado` to make blocking visible. The checklist must name the predecessor, the criterion that releases the workstream, and the expected artifact. A linked item does not replace a child item: a child decomposes work; a link represents a relationship between independent issues.

The central relations are: #77 before #31/#32/#33/#35/#48; #47 before #32/#33/#48; #41 before #48; #42 before #32; #58 before the visual decision for #65; and #43/#36 before closing #34. #31 relates to #33 without being forced into a child hierarchy. The team assigns leads and reviewers; previous authorship is not an automatic assignment.

Milestones represent outcomes, not each session or hour. The three stages are Foundation and contracts; Exploration, experiments, and evidence selection; and Validated analysis and final narrative. Dates or checkpoints should be recorded only when decided by the team; flexible remote work should not become an artificial deadline. The current final milestone is the place for the final outcome, not every intermediate task.

## Review checklist

Run `uv sync --frozen`, the tests defined in the issue, `uv run python scripts/render_notebooks.py`, `uv run python scripts/render_notebooks.py --check`, `marimo check`, and the top-to-bottom smoke run. Check translation pairs, bounded outputs, manifest, CI, and real Molab execution; an HTTP 200 preview does not prove execution. Record failures with pipeline, SHA, job, and first trace.

Do not close an issue or mark it `Finalizado` merely because code exists. Require acceptance criteria, CI, artifacts, caveats, handoff, and human review. Integration is the last workstream and should include only validated evidence or explicitly labeled prototypes.
