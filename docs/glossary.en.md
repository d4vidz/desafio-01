# Project glossary

The terms below must be used consistently in notebooks, issues, MRs, and evidence briefs.

| Term | Operational definition |
| --- | --- |
| **physical row** | A row present in the source CSV; the same track may repeat. |
| **canonical track** | One observation per `track_id` in the `tracks` table; used for features, PCA, and clustering. |
| **membership** | An explicit track–genre edge in `track_genres`; one track may have several. |
| **collaboration** | A track with more than one artist under the declared parsing rule. |
| **popularity** | Observed 0–100 score in the snapshot; not a future-success forecast. |
| **feature** | A variable used to describe or model an observation. |
| **human panel** | A provisional feature set chosen for hypothesis and interpretation. |
| **automated pool** | Additional candidates evaluated by selection/modeling methods without arbitrary pre-removal. |
| **multi-hot** | A binary representation of categorical memberships. |
| **PPMI** | Positive Pointwise Mutual Information computed from declared co-occurrences and marginals. |
| **OOV** | A category outside the vocabulary fitted on training data; it must have an explicit fallback. |
| **PCA** | Linear reduction projecting standardized variables into components and loadings. |
| **clustering** | Exploratory grouping; it is called robust only if it passes the stability gate. |
| **artist split** | A partition preventing an artist seen in training from appearing in the primary test. |
| **leakage** | Test, future, or target information improperly reaching training. |
| **MAE** | Mean absolute error; this project’s primary prediction metric. |
| **claim ceiling** | The strongest claim allowed by population, design, evidence, and limitations. |
| **prototype** | An unvalidated visual/methodological exploration, not a final claim. |
| **evidence brief** | A reproducible summary of question, method, result, uncertainty, and limit. |
| **manifest** | Record of hashes, environment, execution, artifacts, and notebook warnings. |
| **Molab preview** | Temporary URL for viewing/running a notebook; not the canonical source. |

When a term could have more than one interpretation, state the rule in the notebook and issue. See also [data-contract.md](data-contract.md) and [feature-roles.md](feature-roles.md).
