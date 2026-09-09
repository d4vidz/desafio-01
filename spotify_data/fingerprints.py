"""Bounded, deterministic nearest-neighbour diagnostics for audio vectors.

Artist and track identifiers are retained only in the returned audit table.  They
never enter the distance calculation or the candidate restriction, except for
the optional genre filter.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


DEFAULT_AUDIO_FEATURES = (
    "danceability", "energy", "loudness", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence", "tempo", "duration_ms",
)


@dataclass(frozen=True)
class NeighbourDiagnostic:
    """Summary and bounded per-query evidence for a fingerprint diagnostic."""

    summary: pl.DataFrame
    audit: pl.DataFrame
    feature_columns: tuple[str, ...]
    duplicate_tolerance: float
    same_genre: bool

    def to_polars(self) -> pl.DataFrame:
        """Return the compact aggregate report (convenient notebook boundary)."""

        return self.summary


def _validate_inputs(
    frame: pl.DataFrame,
    feature_columns: tuple[str, ...],
    *,
    id_column: str,
    artist_column: str,
    genre_column: str | None,
    duplicate_tolerance: float,
    max_queries: int,
    max_candidates: int,
) -> None:
    if not isinstance(frame, pl.DataFrame):
        raise TypeError("frame must be a Polars DataFrame")
    if not feature_columns:
        raise ValueError("feature_columns must not be empty")
    required = [*feature_columns, id_column, artist_column]
    if genre_column is not None:
        required.append(genre_column)
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    non_numeric = [
        column for column in feature_columns
        if not frame.schema[column].is_numeric()
    ]
    if non_numeric:
        raise TypeError(f"Audio feature columns must be numeric: {non_numeric}")
    if frame.height == 0:
        raise ValueError("frame must contain at least one row")
    if frame[id_column].n_unique() != frame.height:
        raise ValueError(f"{id_column} must identify one canonical row")
    if not isinstance(max_queries, int) or isinstance(max_queries, bool) or max_queries < 1:
        raise ValueError("max_queries must be a positive integer")
    if (
        not isinstance(max_candidates, int)
        or isinstance(max_candidates, bool)
        or not 2 <= max_candidates <= 100_000
    ):
        raise ValueError("max_candidates must be an integer between 2 and 100000")
    if not np.isfinite(duplicate_tolerance) or duplicate_tolerance < 0:
        raise ValueError("duplicate_tolerance must be finite and non-negative")
    values = frame.select(feature_columns).to_numpy()
    if not np.isfinite(values.astype(np.float64)).all():
        raise ValueError("audio features must contain only finite values")


def _stable_order(frame: pl.DataFrame, columns: tuple[str, ...], id_column: str) -> pl.DataFrame:
    # Sorting by all available values makes sampling and tie-breaking independent
    # of the physical input order.  Null audit fields are valid and sort last.
    tie_breakers = tuple(column for column in frame.columns if column not in columns)
    return frame.sort([*columns, *tie_breakers], nulls_last=True)


def diagnose_audio_neighbours(
    frame: pl.DataFrame,
    *,
    feature_columns: tuple[str, ...] = DEFAULT_AUDIO_FEATURES,
    id_column: str = "track_id",
    artist_column: str = "artists",
    genre_column: str | None = "track_genre",
    duplicate_tolerance: float = 0.0,
    same_genre: bool = False,
    max_queries: int = 500,
    max_candidates: int = 20_000,
    seed: int = 2026,
) -> NeighbourDiagnostic:
    """Measure same-artist nearest-neighbour rates before and after exclusions.

    At most ``max_queries`` rows are selected after a stable total sort.  For
    each query, the candidate with minimum Euclidean distance is reported.  The
    baseline excludes only the query row itself.  The post-exclusion candidate
    pool removes every *other* vector whose L-infinity distance from the query
    is at most ``duplicate_tolerance`` (thus tolerance 0 removes exact copies).
    ``same_genre=True`` restricts both pools to rows with the same non-null genre.
    Queries with no eligible post-exclusion candidate are retained in the audit
    and excluded from that rate's denominator.
    """

    feature_columns = tuple(feature_columns)
    if same_genre and genre_column is None:
        raise ValueError("genre_column is required when same_genre=True")
    required_genre = genre_column if same_genre else None
    _validate_inputs(
        frame, feature_columns, id_column=id_column, artist_column=artist_column,
        genre_column=required_genre, duplicate_tolerance=duplicate_tolerance,
        max_queries=max_queries, max_candidates=max_candidates,
    )
    order_columns = tuple(
        dict.fromkeys(
            [
                id_column,
                artist_column,
                *feature_columns,
                *([required_genre] if required_genre else []),
            ]
        )
    )
    ordered = _stable_order(frame, order_columns, id_column)
    if ordered.height > max_candidates:
        ordered = ordered.sample(
            n=max_candidates, seed=seed, shuffle=True
        )
    query_count = min(max_queries, ordered.height)
    queries = ordered.head(query_count)
    raw_values = ordered.select(feature_columns).to_numpy().astype(np.float64)
    values = StandardScaler().fit_transform(raw_values)
    query_values = values[:query_count]
    query_indices = np.arange(query_count, dtype=np.int64)

    audit_rows: list[dict[str, object]] = []
    for qpos, vector in zip(query_indices, query_values):
        qpos = int(qpos)
        candidate_mask = np.ones(ordered.height, dtype=bool)
        candidate_mask[qpos] = False
        if same_genre:
            query_genre = queries[qpos, genre_column]  # type: ignore[index]
            if query_genre is None:
                candidate_mask[:] = False
            else:
                candidate_mask &= ordered.get_column(genre_column).to_numpy() == query_genre  # type: ignore[arg-type]
        candidate_positions = np.flatnonzero(candidate_mask)

        def nearest(positions: np.ndarray) -> tuple[int | None, float | None]:
            if len(positions) == 0:
                return None, None
            model = NearestNeighbors(n_neighbors=1, metric="euclidean", algorithm="brute")
            model.fit(values[positions])
            distance, local = model.kneighbors(vector.reshape(1, -1), return_distance=True)
            best_distance = float(distance[0, 0])
            tied = positions[np.isclose(np.linalg.norm(values[positions] - vector, axis=1), best_distance, rtol=1e-12, atol=1e-12)]
            best_position = int(tied.min())
            return best_position, best_distance

        before_position, before_distance = nearest(candidate_positions)
        near_duplicate = np.max(
            np.abs(raw_values[candidate_positions] - raw_values[qpos]), axis=1
        ) <= duplicate_tolerance if len(candidate_positions) else np.array([], dtype=bool)
        after_positions = candidate_positions[~near_duplicate]
        after_position, after_distance = nearest(after_positions)

        row = {
            "query_position": int(qpos),
            "query_id": queries[qpos, id_column],
            "query_artist": queries[qpos, artist_column],
            "before_neighbour_id": ordered[before_position, id_column] if before_position is not None else None,
            "before_neighbour_artist": ordered[before_position, artist_column] if before_position is not None else None,
            "before_distance": before_distance,
            "before_same_artist": bool(before_position is not None and ordered[before_position, artist_column] == queries[qpos, artist_column]),
            "after_neighbour_id": ordered[after_position, id_column] if after_position is not None else None,
            "after_neighbour_artist": ordered[after_position, artist_column] if after_position is not None else None,
            "after_distance": after_distance,
            "after_same_artist": bool(after_position is not None and ordered[after_position, artist_column] == queries[qpos, artist_column]),
            "after_candidate_count": int(len(after_positions)),
        }
        audit_rows.append(row)

    audit = pl.DataFrame(audit_rows)
    before_valid = audit.filter(pl.col("before_neighbour_id").is_not_null())
    after_valid = audit.filter(pl.col("after_neighbour_id").is_not_null())
    summary = pl.DataFrame({
        "n_queries": [query_count],
        "before_same_artist_rate": [before_valid["before_same_artist"].mean() if before_valid.height else None],
        "after_same_artist_rate": [after_valid["after_same_artist"].mean() if after_valid.height else None],
        "before_eligible_queries": [before_valid.height],
        "after_eligible_queries": [after_valid.height],
        "excluded_query_count": [query_count - after_valid.height],
        "candidate_rows": [ordered.height],
        "seed": [seed],
        "distance_standardized": [True],
    })
    return NeighbourDiagnostic(summary, audit, feature_columns, duplicate_tolerance, same_genre)


# American spelling is a small convenience for callers using sklearn's name.
diagnose_audio_neighbors = diagnose_audio_neighbours
