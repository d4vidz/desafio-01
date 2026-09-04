# Analytical work governance

This project separates three GitLab work-item types:

1. **Question**: what we want to learn.
2. **Specification**: which decisions, contracts, and evidence the implementation must respect.
3. **Delivery**: reviewable code, analysis, visualization, or documentation.

Use the templates in `.gitlab/issue_templates/` and the merge-request template in `.gitlab/merge_request_templates/`. Every issue should state a question or objective, grain, definitions, expected evidence, acceptance criteria, and caveats. A delivery also records validation commands and links to its question and specification.

## Labels and priority

Use labels to represent separate dimensions rather than turning the title into an inventory:

- `tipo::pergunta`, `tipo::especificação`, `tipo::entrega`, `tipo::mudança`;
- `evidência::descritiva`, `comparativa`, `relacional`, `contextual`, `exploratória`, `explicativa`, `preditiva`;
- `área::qualidade-de-dados`, `camada-de-dados`, `visualização`, `modelagem`, `documentação`, `revisão`;
- `fluxo::pronto`, `em-andamento`, `bloqueado`, `revisão`;
- `prioridade::1`, `prioridade::2`, `prioridade::3`.

`prioridade::1` blocks correctness or the final delivery; `prioridade::2` matters for the selected story; `prioridade::3` is exploration or follow-up. Historical labels must not be renamed or removed without approval. Older issues remain valid as a question bank; propose a template migration to the author before editing their text.

Each new issue should use at most one `tipo::`, one `fluxo::`, and one `prioridade::` label; it may use multiple `evidência::` and `área::` labels when needed. Milestones represent outcomes, not meetings. Assignment represents responsibility, links represent dependencies, and checklists represent acceptance criteria.

Provenance labels named `proposta::<source-or-round>` are temporary: they locate proposals during review and do not replace `tipo::`, `fluxo::`, or `área::`. After the decision is recorded, remove them from issues and retire them until another explicit round. Create a new namespace only when there is a recurring filtering need, a clear definition, no duplicate dimension, and team approval.

### Label palette and descriptions

Colors identify the dimension before the value: blue for type, teal for evidence, purple for area, semantic colors for workflow, and red/orange/yellow for priority. GitLab configuration should follow this source of truth:

| Label | Color | Short description |
| --- | --- | --- |
| `tipo::pergunta` | `#1F75CB` | Analytical question that guides one or more deliverables. |
| `tipo::especificação` | `#0B5CAD` | Implementation contract and acceptance criteria. |
| `tipo::entrega` | `#428BCA` | Reviewable code, analysis, visualization, or documentation artifact. |
| `tipo::mudança` | `#6F42C1` | Recorded scope, contract, or correction change. |
| `evidência::descritiva` | `#008B8B` | Characterizes a distribution, frequency, quality, or dataset summary. |
| `evidência::comparativa` | `#009A9A` | Compares groups, slices, or conditions with explicit denominators. |
| `evidência::relacional` | `#00A6A6` | Examines association or structure among variables or entities. |
| `evidência::contextual` | `#087F8C` | Interprets results using external context and documented caveats. |
| `evidência::exploratória` | `#00B3B3` | Performs hypothesis-generating screening without a confirmatory claim. |
| `evidência::explicativa` | `#006D77` | Tests competing mechanisms or explanations without overstating causality. |
| `evidência::preditiva` | `#005F73` | Evaluates prediction on held-out data with a baseline and uncertainty. |
| `área::qualidade-de-dados` | `#7B2CBF` | Validity, completeness, duplicates, ranges, and cleaning. |
| `área::camada-de-dados` | `#5A189A` | Schema, grains, DuckDB, Polars, and shared transformations. |
| `área::visualização` | `#9D4EDD` | Charts, widgets, interactions, and visual narrative. |
| `área::modelagem` | `#C77DFF` | Features, experiments, models, and held-out evaluation. |
| `área::documentação` | `#815AC0` | Guides, contracts, handoffs, and supporting material. |
| `área::revisão` | `#3C096C` | Independent audit, integration, and quality gate. |
| `fluxo::pronto` | `#108548` | Scope is sufficient for someone to start work. |
| `fluxo::em-andamento` | `#1F75CB` | A lead is actively working on the issue. |
| `fluxo::bloqueado` | `#C91C00` | A dependency or decision prevents material progress. |
| `fluxo::revisão` | `#D99530` | Implementation or proposal awaits review or acceptance. |
| `prioridade::1` | `#C91C00` | Blocks correctness, integration, or final delivery. |
| `prioridade::2` | `#D99530` | Important to the selected narrative or scope. |
| `prioridade::3` | `#EAC54F` | Non-blocking exploration or follow-up. |

Every GitLab label should have its own description even when it shares its dimension color. `evidência::*` is documentation shorthand; all seven labels retain individual names and describe their corresponding class.

## Specifications, scope, and changes

A specification is an implementation contract: it defines required decisions, interfaces, invariants, edge cases, non-goals, validation, and the definition of done. A delivery may choose the implementation, but must record any deviation.

Scope moves through checkpoints. After a lock, a new question becomes a proposal/follow-up unless it is a critical quality or reproducibility correction. Every change records requester, decision owner, reason, impact, removed or deferred work, new acceptance criterion, and date. Critical corrections may cross the lock when they prevent an incorrect or irreproducible result.

Approved specifications are required for shared or high-risk contracts: schema/grain, validation, headline claims, graph features, and final notebook structure. A small isolated exploration may move directly from `pergunta::` to `entrega::`. Every delivery must link to the question and specification that authorize it.

The v0.1 feature lock separates the human panel from the modeling candidate pool. The human panel uses `danceability`, `energy`, `valence`, `acousticness`, `instrumentalness`, and `speechiness`; `loudness`, `liveness`, `tempo`, and `duration_ms` remain sensitivity/context variables. No column is permanently removed by this lock. Later changes require a decision record.

The recommended ownership model is lead + reviewer, with an integrator for artifacts spanning notebooks. Prior authorship may guide an offer of continuity but does not determine automatic assignment.

## Evidence and review

Always state whether the analysis shows association, comparison, prediction, or causality. Do not use “impacts” or “causes” when the design supports only association. Unit, aggregation, sample, uncertainty, selection, missingness, and limitations must accompany each claim.

The final Marimo notebook must be reproducible, use small cells, and keep outputs bounded. The CSV is the versioned source; DuckDB is ephemeral and rebuilt at runtime; Polars is preferred for typed transformations. Charts and networks need an explicit question, grain, encoding, aggregation, and render limit.

The schedule uses `America/Sao_Paulo` timestamps in checkpoint issues. Flexible remote-work windows receive no due date. For this cycle: triage by 12:00 on 31/08; feature lock at 16:00; candidate questions, methods, and claim classes frozen at 18:00; final claim selection at 10:00 on 02/09; deliverables preferred by 12:00; audit at 16:00; hard deadline at 18:00. Remote work between locks is allowed only within the frozen scope and does not create a new status obligation.

## Bilingual documentation

Portuguese is canonical. The pairs listed in `docs/translation-pairs.json` keep the English translation synchronized using the canonical file hash. Run `python scripts/check_translation_pairs.py` before opening a merge request. The checker does not judge translation quality; it prevents a translation from becoming silently stale.
