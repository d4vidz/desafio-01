import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = tuple((ROOT / "notebooks").rglob("*.py"))


def test_notebooks_do_not_sample_unordered_frames_directly():
    offenders = []
    for notebook in NOTEBOOKS:
        source = notebook.read_text(encoding="utf-8")
        if ".sample(" in source:
            offenders.append(notebook.relative_to(ROOT).as_posix())
    assert offenders == []


def test_notebook_top_n_queries_have_explicit_tie_breakers():
    ambiguous_patterns = (
        re.compile(r"ORDER BY\s+(?:count|COUNT)\(DISTINCT track_id\) DESC\s+LIMIT"),
        re.compile(r"ORDER BY\s+w DESC\s+LIMIT"),
    )
    offenders = []
    for notebook in NOTEBOOKS:
        source = notebook.read_text(encoding="utf-8")
        if any(pattern.search(source) for pattern in ambiguous_patterns):
            offenders.append(notebook.relative_to(ROOT).as_posix())
    assert offenders == []
