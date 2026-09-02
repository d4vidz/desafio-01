# Categorical representations and genre embeddings v0.1

This document turns issue #47 into a small, reproducible protocol. The goal is not to claim that genre causes `popularity`; it is to test whether representations add stable, interpretable held-out information.

## Representation ladder

1. **No genre**: baseline with audited audio and categorical fields.
2. **Multi-hot**: one column per genre known in training; genres absent from training receive zeros (explicit OOV policy).
3. **PPMI + TruncatedSVD embedding**: genre co-occurrence by track, PPMI, and SVD. The primary version has 8 dimensions; 4 and 16 are sensitivities.

PPMI is fit only on training tracks. A multigenre track receives the mean of its known genre vectors. During validation, the vocabulary, co-occurrence matrix, and SVD are also fold-local; the test set is never used to fit the embedding.

## Remaining categoricals

- `explicit` and `mode`: binary.
- `key`: `sin`/`cos` is primary because the scale is circular; one-hot is a sensitivity.
- `time_signature`: nominal one-hot, with an audit of 0/1 values present in the snapshot despite the expected 3–7 description.
- `artists`, `album_name`, `track_name`, and `track_id`: identifiers/context. They are not direct predictors. Artist aggregates appear only in fold-local ablations with an explicit OOV fallback.

## Genre audio profiles

The complementary EDA view uses all memberships. For each genre, it computes the 10th/25th/50th/75th/90th quantiles of ten continuous features, for 50 dimensions; then applies RobustScaler and PCA. Sensitivities are single-genre tracks and fractional `1/k` weights for a track with `k` genres.

## Decision gate

PPMI is promoted to predictive evidence only if it beats multi-hot on the same model, split, and repetitions, with at least a 0.5-point MAE reduction and a paired artist-clustered bootstrap interval excluding zero. If it fails, the result is a bounded genre–artist feasibility pilot and scorecard; no graph database, GNN, Node2Vec, or artist-model pivot starts in this delivery.

## Notebook use

- `notebooks/data_contract_audit.py` documents the contract and learns no representations.
- `notebooks/explorations/genre_representations.py` shows the ladder and audio profiles for EDA.
- `notebooks/explorations/popularity_validation.py` is the predictive validation; transformations must be fit inside each fold.
- `notebooks/spotify_analysis.py` receives only reviewed, bounded results.
