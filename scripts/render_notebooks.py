"""Render the canonical Marimo notebooks to committed HTML snapshots."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "artifacts" / "notebooks" / "html"
NOTEBOOKS = (
    ROOT / "notebooks" / "data_contract_audit.py",
    ROOT / "notebooks" / "explorations" / "popularity_associations.py",
    ROOT / "notebooks" / "explorations" / "genre_representations.py",
    ROOT / "notebooks" / "explorations" / "musical_structure.py",
    ROOT / "notebooks" / "explorations" / "popularity_validation.py",
    ROOT / "notebooks" / "spotify_analysis.py",
)


def output_path(notebook: Path, directory: Path) -> Path:
    """Return the stable HTML name for a canonical notebook."""

    return directory / f"{notebook.stem}.html"


def render(notebook: Path, output: Path) -> None:
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


def source_digest(notebook: Path) -> str:
    """Return the digest used to tie a rendered artifact to its source."""

    return hashlib.sha256(notebook.read_bytes()).hexdigest()


def stamp_snapshot(output: Path, notebook: Path) -> None:
    """Add a small provenance marker without touching Marimo's generated body."""

    marker = f"<!-- canonical-notebook-sha256: {source_digest(notebook)} -->\n".encode()
    output.write_bytes(marker + output.read_bytes())


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
                render(notebook, rendered)
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
        print("Committed Marimo HTML snapshots are current.")
        return 0

    for notebook in NOTEBOOKS:
        output = output_path(notebook, HTML_DIR)
        print(f"Rendering {notebook.relative_to(ROOT)} -> {output.relative_to(ROOT)}", flush=True)
        render(notebook, output)
    print(f"Rendered {len(NOTEBOOKS)} notebooks to {HTML_DIR.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
