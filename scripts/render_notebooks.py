"""Render the canonical Marimo notebooks to committed HTML snapshots."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "artifacts" / "notebooks" / "html"
MANIFEST_PATH = ROOT / "artifacts" / "notebooks" / "manifest.json"
SOURCE_PATH = ROOT / "data" / "raw" / "spotify_tracks.csv"
LOCK_PATH = ROOT / "uv.lock"
OUTPUT_LIMIT_BYTES = 5_000_000
NOTEBOOKS = (
    ROOT / "notebooks" / "data_contract_audit.py",
    ROOT / "notebooks" / "explorations" / "popularity_associations.py",
    ROOT / "notebooks" / "explorations" / "genre_representations.py",
    ROOT / "notebooks" / "explorations" / "musical_structure.py",
    ROOT / "notebooks" / "explorations" / "popularity_validation.py",
    ROOT / "notebooks" / "spotify_analysis.py",
)

NOTEBOOK_METADATA = {
    "data_contract_audit": (
        "Spotify — auditoria do contrato de dados",
        "Reconstrução auditável da camada DuckDB/Polars e de seus grains.",
    ),
    "popularity_associations": (
        "Spotify — associações com popularidade",
        "Protótipo estatístico de associações com a popularidade observada.",
    ),
    "genre_representations": (
        "Spotify — representações de gênero",
        "Multi-hot, PPMI/SVD, perfis de áudio e visualizações de gênero.",
    ),
    "musical_structure": (
        "Spotify — estrutura musical",
        "PCA, loadings e estabilidade de clustering das audio features.",
    ),
    "popularity_validation": (
        "Spotify — validação preditiva",
        "Protótipo de generalização da popularidade para artistas não vistos.",
    ),
    "spotify_analysis": (
        "Spotify — análise integrada",
        "Contrato, exploração e protótipos integrados com limites de evidência.",
    ),
}

EVIDENCE_STATUS_VALUES = {
    "INFRASTRUCTURE": "infraestrutura",
    "PROTOTYPE": "protótipo",
    "COMPLETE_EXPERIMENT": "experimento_completo",
    "VALIDATED_EVIDENCE": "evidência_validada",
}


def output_path(notebook: Path, directory: Path) -> Path:
    """Return the stable HTML name for a canonical notebook."""

    return directory / f"{notebook.stem}.html"


def render(notebook: Path, output: Path) -> list[str]:
    """Execute and export one notebook, including source code for auditability."""

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "marimo",
        "export",
        "html",
        str(notebook),
        "--include-code",
        "--no-sandbox",
        "-o",
        str(output),
        "-f",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode:
        raise RuntimeError(
            f"Notebook export failed for {notebook}:\n{result.stdout}\n{result.stderr}"
        )
    stamp_snapshot(output, notebook)
    return [line.strip() for line in result.stderr.splitlines() if line.strip()]


def source_digest(notebook: Path) -> str:
    """Return the digest used to tie a rendered artifact to its source."""

    return file_digest(notebook, normalize_newlines=True)


def file_digest(path: Path, *, normalize_newlines: bool = False) -> str:
    """Return a stable SHA-256 digest for an artifact or text source."""

    content = path.read_bytes()
    if normalize_newlines:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def git_value(*args: str) -> str | None:
    """Read bounded repository metadata without making rendering depend on Git."""

    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def declared_evidence_statuses(notebook: Path) -> list[str]:
    """Return EvidenceStatus members declared by a notebook, in source order."""

    source = notebook.read_text(encoding="utf-8")
    members = list(dict.fromkeys(re.findall(r"EvidenceStatus\.([A-Z_]+)", source)))
    return [EVIDENCE_STATUS_VALUES.get(member, member) for member in members]


def notebook_configuration(notebook: Path) -> dict[str, object]:
    """Extract small, review-oriented configuration fields from source."""

    source = notebook.read_text(encoding="utf-8")
    generated = re.search(r'__generated_with\s*=\s*"([^"]+)"', source)
    width = re.search(r"marimo\.App\(width=\"([^\"]+)\"\)", source)
    seeds = sorted({int(value) for value in re.findall(r"(?:seed|random_state)\s*=\s*(\d+)", source)})
    return {
        "generated_with": generated.group(1) if generated else None,
        "app_width": width.group(1) if width else None,
        "declared_integer_seeds": seeds,
        "output_limit_bytes_per_cell": OUTPUT_LIMIT_BYTES,
    }


def build_manifest(
    html_directory: Path,
    outcomes: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build the review manifest from notebook sources and rendered HTML files."""

    entries = []
    for notebook in NOTEBOOKS:
        html = output_path(notebook, html_directory)
        statuses = declared_evidence_statuses(notebook)
        if not statuses:
            raise RuntimeError(
                f"Notebook does not declare an EvidenceStatus: {notebook.relative_to(ROOT)}"
            )
        outcome = (outcomes or {}).get(notebook.as_posix(), {})
        entries.append(
            {
                "notebook": notebook.relative_to(ROOT).as_posix(),
                "notebook_sha256": source_digest(notebook),
                "html": html.relative_to(ROOT).as_posix()
                if html_directory == HTML_DIR
                else html.name,
                "html_sha256": file_digest(html),
                "html_bytes": html.stat().st_size,
                "declared_evidence_statuses": statuses,
                "execution_status": outcome.get("execution_status", "passed"),
                "warnings": outcome.get("warnings", []),
                "configuration": notebook_configuration(notebook),
            }
        )
    return {
        "version": 1,
        "source": {
            "path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "sha256": file_digest(SOURCE_PATH, normalize_newlines=True),
            "contract_version": "0.1",
        },
        "repository": {
            "commit_at_render": os.environ.get("CI_COMMIT_SHA") or git_value("rev-parse", "HEAD"),
            "ref_at_render": os.environ.get("CI_COMMIT_REF_NAME") or git_value("branch", "--show-current"),
            "working_tree_dirty_at_render": bool(git_value("status", "--porcelain")),
            "environment_lock_sha256": file_digest(LOCK_PATH),
        },
        "environment": {
            "python": platform.python_version(),
            "marimo": importlib.metadata.version("marimo"),
            "platform": platform.platform(),
        },
        "notebooks": entries,
    }


def write_manifest(
    html_directory: Path,
    destination: Path,
    outcomes: dict[str, dict[str, object]] | None = None,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_manifest(html_directory, outcomes), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def stamp_snapshot(output: Path, notebook: Path) -> None:
    """Add provenance and reader-facing metadata to Marimo's generated body."""

    title, description = NOTEBOOK_METADATA[notebook.stem]
    body = output.read_text(encoding="utf-8")
    body = body.replace('<html lang="en">', '<html lang="pt-BR">', 1)
    body = body.replace(
        '<meta name="description" content="a marimo app" />',
        f'<meta name="description" content="{description}" />',
        1,
    )
    body = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", body, count=1)
    marker = f"<!-- canonical-notebook-sha256: {source_digest(notebook)} -->\n"
    output.write_text(marker + body, encoding="utf-8")


def snapshot_digest(path: Path) -> str | None:
    """Read a snapshot's source digest from its first-line provenance marker."""

    first_line = path.open("rb").readline().decode("ascii", errors="ignore").strip()
    prefix = "<!-- canonical-notebook-sha256: "
    suffix = " -->"
    if first_line.startswith(prefix) and first_line.endswith(suffix):
        return first_line[len(prefix) : -len(suffix)]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="render to a temporary directory and fail if committed HTML is stale",
    )
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="spotify-marimo-render-") as temporary:
            temporary_dir = Path(temporary)
            for notebook in NOTEBOOKS:
                committed = output_path(notebook, HTML_DIR)
                rendered = output_path(notebook, temporary_dir)
                print(f"Checking {notebook.relative_to(ROOT)}", flush=True)
                warnings = render(notebook, rendered)
                if not committed.is_file():
                    print(f"ERROR: missing committed snapshot: {committed}")
                    return 1
                expected = source_digest(notebook)
                if snapshot_digest(committed) != expected:
                    print(f"ERROR: stale committed snapshot: {committed}")
                    return 1
                if snapshot_digest(rendered) != expected:
                    print(f"ERROR: export provenance mismatch: {rendered}")
                    return 1
                if warnings:
                    print(f"WARNING: export emitted warnings for {notebook.relative_to(ROOT)}")
            if not MANIFEST_PATH.is_file():
                print(f"ERROR: missing notebook manifest: {MANIFEST_PATH}")
                return 1
            committed_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            current_manifest = build_manifest(HTML_DIR)
            committed_entries = {entry["notebook"]: entry for entry in committed_manifest["notebooks"]}
            for current in current_manifest["notebooks"]:
                committed = committed_entries.get(current["notebook"])
                if committed is None:
                    print(f"ERROR: notebook missing from manifest: {current['notebook']}")
                    return 1
                for field in (
                    "notebook_sha256",
                    "html_sha256",
                    "html_bytes",
                    "declared_evidence_statuses",
                    "execution_status",
                    "configuration",
                ):
                    if committed.get(field) != current[field]:
                        print(f"ERROR: stale manifest field {field}: {current['notebook']}")
                        return 1
        print("Committed Marimo HTML snapshots are current.")
        return 0

    outcomes: dict[str, dict[str, object]] = {}
    for notebook in NOTEBOOKS:
        output = output_path(notebook, HTML_DIR)
        print(f"Rendering {notebook.relative_to(ROOT)} -> {output.relative_to(ROOT)}", flush=True)
        warnings = render(notebook, output)
        outcomes[notebook.as_posix()] = {
            "execution_status": "passed",
            "warnings": warnings,
        }
    write_manifest(HTML_DIR, MANIFEST_PATH, outcomes)
    print(f"Rendered {len(NOTEBOOKS)} notebooks to {HTML_DIR.relative_to(ROOT)}.")
    print(f"Wrote review manifest to {MANIFEST_PATH.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
