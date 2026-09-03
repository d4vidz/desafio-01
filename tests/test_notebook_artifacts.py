import json

from scripts.render_notebooks import (
    HTML_DIR,
    MANIFEST_PATH,
    NOTEBOOKS,
    build_manifest,
    declared_evidence_statuses,
)


def test_every_canonical_notebook_declares_evidence_maturity():
    for notebook in NOTEBOOKS:
        assert declared_evidence_statuses(notebook), notebook


def test_committed_manifest_matches_current_sources_and_html():
    assert MANIFEST_PATH.is_file()
    committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    current = build_manifest(HTML_DIR)
    committed_entries = {entry["notebook"]: entry for entry in committed["notebooks"]}
    assert set(committed_entries) == {entry["notebook"] for entry in current["notebooks"]}
    for entry in current["notebooks"]:
        stored = committed_entries[entry["notebook"]]
        for field in (
            "notebook_sha256",
            "html_sha256",
            "html_bytes",
            "declared_evidence_statuses",
            "execution_status",
            "configuration",
        ):
            assert stored[field] == entry[field]
        assert isinstance(stored["warnings"], list)
        assert stored["execution_status"] == "passed"
