# Feature roles contract v0.1

This document guides the first analysis cycle. It does not remove columns from the CSV or claim that a feature is causally relevant. It separates what deserves immediate human interpretation from what should remain available to automated experiments.

## Outcome and grain

- Primary outcome: observed `popularity` in the catalogue.
- Primary grain: one canonical row per `track_id`.
- `popularity` never enters the predictors for its own task.
- IDs, track names, artist names, and identifier fields are context, not direct predictors.

## v0.1 roles

| Role | Columns | Use |
| --- | --- | --- |
| Human panel | `danceability`, `energy`, `valence`, `acousticness`, `instrumentalness`, `speechiness` | Main associations, comparisons, and narrative about popularity. |
| Sensitivity/context | `loudness`, `liveness`, `tempo`, `duration_ms` | Repeats, redundancy controls, and automated candidate pool. |
| Categorical | `explicit`, `key`, `mode`, `time_signature` | Comparisons and categorical encoding; do not silently mix with continuous correlations. |
| Grouping/context | `artists`, `track_genre`, `album_name`, `track_name` | Grain, stratification, validation, joins, and contextual interpretation. |
| Automated candidates | All valid audio features and categorical fields | Regularized selection, permutation importance, and held-out stability. |
| Controlled derived | Artist and graph aggregates | Fold-local ablations only, with an explicit unseen-artist fallback. |

## Evidence protocol

1. The human panel uses effect sizes, intervals, and genre heterogeneity; isolated p-values do not select features.
2. Primary hypotheses use artist-grouped discovery/confirmation.
3. Exploratory screening declares multiplicity and uses FDR when appropriate.
4. The predictive claim is estimation of observed popularity on held-out data, not temporal forecasting.
5. Random track splits are optimistic diagnostics only; unseen-artist splitting is primary.
6. No feature is permanently removed by this contract. Changes require a record of evidence, impact, and removed or deferred work.

## Initial hypotheses

- Human-panel feature associations with popularity may be small and heterogeneous across genres.
- `energy`, `loudness`, and `acousticness` should be treated as a potentially redundant block.
- Audio may carry artist fingerprints even without the artist name; therefore a random split is not sufficient evidence of generalization.
- Graph-derived features enter the narrative only if they improve the held-out metric on the same split and model.
