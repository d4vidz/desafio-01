"""Execute bounded Marimo notebooks in headless mode for CI.

``marimo check`` validates the cell graph; this smoke test executes the
notebooks with their real repository input and catches runtime-only failures.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = (
    ROOT / "notebooks" / "data_contract_audit.py",
    ROOT / "notebooks" / "explorations" / "popularity_associations.py",
    ROOT / "notebooks" / "explorations" / "genre_representations.py",
    ROOT / "notebooks" / "explorations" / "musical_structure.py",
    ROOT / "notebooks" / "explorations" / "popularity_validation.py",
    ROOT / "notebooks" / "spotify_analysis.py",
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="spotify-marimo-smoke-") as output_dir:
        for index, notebook in enumerate(NOTEBOOKS):
            output = Path(output_dir) / f"notebook-{index}.html"
            print(f"Smoke notebook {index + 1}/{len(NOTEBOOKS)}: {notebook.name}", flush=True)
            result = subprocess.run(
                [sys.executable, "-m", "marimo", "export", "html", str(notebook), "--no-include-code", "-o", str(output), "-f"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode:
                print(f"Notebook failed: {notebook}\n{result.stdout}\n{result.stderr}", file=sys.stderr)
                return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
