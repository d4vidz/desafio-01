"""Update the immutable repository snapshot used by Molab notebook bootstraps.

Molab's GitHub-backed preview provides the selected notebook file, not the
whole repository tree. Each notebook therefore downloads a pinned archive
that supplies the shared package and CSV. This command keeps that pin
consistent across all canonical notebooks.
"""

from __future__ import annotations

import argparse
import re
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
SNAPSHOT_PATTERN = re.compile(r'(?m)^(?P<indent>\s*)snapshot = "(?P<sha>[0-9a-f]{40})"$')


def update_notebook(notebook: Path, commit: str) -> bool:
    """Replace exactly one Molab context pin and report whether it changed."""

    source = notebook.read_text(encoding="utf-8")
    matches = list(SNAPSHOT_PATTERN.finditer(source))
    if len(matches) != 1:
        raise ValueError(
            f"Expected one Molab snapshot pin in {notebook.relative_to(ROOT)}, "
            f"found {len(matches)}"
        )
    match = matches[0]
    replacement = f'{match.group("indent")}snapshot = "{commit}"'
    updated = source[: match.start()] + replacement + source[match.end() :]
    if updated == source:
        return False
    notebook.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "commit",
        help="40-character Git commit that contains the shared spotify_data package and CSV",
    )
    args = parser.parse_args()
    commit = args.commit.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        parser.error("commit must be a 40-character hexadecimal Git SHA")

    changed = 0
    for notebook in NOTEBOOKS:
        if update_notebook(notebook, commit):
            changed += 1
        print(f"{notebook.relative_to(ROOT)} -> {commit}")
    print(f"Updated {changed}/{len(NOTEBOOKS)} Molab context pins.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
