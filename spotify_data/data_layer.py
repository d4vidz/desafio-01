"""Ephemeral DuckDB facade and bounded contract evidence.

The CSV remains the source of truth.  ``build_data_layer`` is intentionally a
small facade over the backwards-compatible ``build_duckdb_layer`` function so
that notebooks can share the same reconstruction and expose its audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import platform
import subprocess
import sys
from typing import Any

import duckdb
import polars as pl

from .data_contract import (
    RAW_COLUMNS,
    build_duckdb_layer,
    load_tracks_raw,
    validate_repeated_track_fields,
    validate_clean_schema,
)

CONTRACT_VERSION = "0.1"


def canonical_file_sha256(path: str | Path) -> str:
    """Hash a text source with platform line endings normalized."""

    data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return sha256(data).hexdigest()


@dataclass(frozen=True)
class DataContractReport:
    """Serializable evidence about one source-to-analytical-layer rebuild."""

    source_path: str
    source_sha256: str
    contract_version: str
    counts: dict[str, int]
    removals: dict[str, int]
    missingness: list[dict[str, Any]]
    ranges: dict[str, dict[str, float | int | None]]
    conflicts: dict[str, int]
    status: str
    code_revision: dict[str, str | None]

    def as_polars(self) -> pl.DataFrame:
        """Return a compact one-row summary suitable for a notebook table."""

        return pl.DataFrame(
            {
                "source_sha256": [self.source_sha256],
                "contract_version": [self.contract_version],
                "status": [self.status],
                "raw_rows": [self.counts["tracks_raw"]],
                "clean_rows": [self.counts["tracks_clean"]],
                "canonical_tracks": [self.counts["tracks"]],
                "genre_edges": [self.counts["track_genres"]],
                "artist_edges": [self.counts["track_artists"]],
                "removed_rows": [self.removals["total"]],
                "popularity_conflicts": [self.conflicts["popularity"]],
            }
        )


@dataclass(frozen=True)
class DataLayer:
    """DuckDB connection plus the report generated from the same snapshot."""

    connection: duckdb.DuckDBPyConnection
    report: DataContractReport


def _revision_metadata() -> dict[str, str | None]:
    commit = os.environ.get("CI_COMMIT_SHA") or os.environ.get("GIT_COMMIT")
    if not commit:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            commit = result.stdout.strip() if result.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            commit = None
    return {
        "git_commit": commit,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "package": "spotify-track-analysis",
    }


def _range_summary(frame: pl.DataFrame, column: str) -> dict[str, float | int | None]:
    values = frame.get_column(column)
    return {
        "min": values.min(),
        "max": values.max(),
        "nulls": values.null_count(),
    }


def _make_report(path: str | Path, connection: duckdb.DuckDBPyConnection) -> DataContractReport:
    raw = load_tracks_raw(path)
    clean = connection.execute("SELECT * FROM tracks_clean").pl()
    validate_clean_schema(clean)
    table_counts = {
        name: int(connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
        for name in ("tracks_raw", "tracks_clean", "tracks", "track_genres", "track_artists")
    }
    missing = [
        {"column": column, "missing_count": raw.get_column(column).null_count(), "missing_fraction": raw.get_column(column).null_count() / raw.height}
        for column in RAW_COLUMNS
    ]
    ranges = {column: _range_summary(raw, column) for column in ("popularity", "duration_ms", "tempo", "loudness")}
    metadata_conflicts = validate_repeated_track_fields(raw)
    conflicts = {
        "popularity": int(connection.execute("SELECT COUNT(*) FROM tracks WHERE popularity_conflict").fetchone()[0]),
        "canonical_metadata": int(metadata_conflicts.height),
    }
    missing_identifier_rows = int(raw.height - raw.filter(
        pl.all_horizontal(pl.col(column).is_not_null() for column in ("artists", "album_name", "track_name"))
    ).height)
    removed = {
        "missing_identifier_rows": missing_identifier_rows,
        "exact_duplicates": int(raw.height - missing_identifier_rows - clean.height),
    }
    removed["total"] = removed["missing_identifier_rows"] + removed["exact_duplicates"]
    invalid_ranges = {
        "popularity": int(raw.filter(~pl.col("popularity").is_between(0, 100)).height),
        "duration_ms": int(raw.filter(pl.col("duration_ms") <= 0).height),
        "tempo": int(raw.filter(pl.col("tempo") <= 0).height),
        "audio_features_0_1": int(raw.filter(
            ~pl.all_horizontal(pl.col(column).is_between(0, 1) for column in ("danceability", "energy", "speechiness", "acousticness", "instrumentalness", "liveness", "valence"))
        ).height),
        "key_0_11": int(raw.filter(~pl.col("key").is_between(0, 11)).height),
        "mode_0_1": int(raw.filter(~pl.col("mode").is_between(0, 1)).height),
    }
    sentinels = {"time_signature_outside_3_7": int(raw.filter(~pl.col("time_signature").is_between(3, 7)).height)}
    status = "ok" if not any(invalid_ranges.values()) and not any(sentinels.values()) else "attention"
    return DataContractReport(
        source_path=str(Path(path).resolve()),
        source_sha256=canonical_file_sha256(path),
        contract_version=CONTRACT_VERSION,
        counts=table_counts,
        removals=removed,
        missingness=missing,
        ranges={**ranges, "invalid_counts": invalid_ranges, "sentinel_counts": sentinels},
        conflicts=conflicts,
        status=status,
        code_revision=_revision_metadata(),
    )


def build_data_layer(
    path: str | Path,
    connection: duckdb.DuckDBPyConnection | None = None,
) -> DataLayer:
    """Rebuild an in-memory layer and return its connection plus audit report."""

    db = build_duckdb_layer(path, connection=connection or duckdb.connect(":memory:"))
    return DataLayer(connection=db, report=_make_report(path, db))


def contract_capsule(report: DataContractReport) -> dict[str, Any]:
    """Return only bounded fields intended for repeated notebook display."""

    return {
        "contrato": report.contract_version,
        "status": report.status,
        "sha256": report.source_sha256[:12] + "…",
        "linhas": report.counts,
        "removidas": report.removals,
        "conflitos_popularity": report.conflicts["popularity"],
        "imputação": "não aplicada; não há missingness de features no snapshot",
    }
