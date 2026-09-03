import json

from scripts.render_notebooks import (
    HTML_DIR,
    MANIFEST_PATH,
    NOTEBOOKS,
    NOTEBOOK_METADATA,
    build_manifest,
    declared_evidence_statuses,
)


def test_every_canonical_notebook_declares_evidence_maturity():
    for notebook in NOTEBOOKS:
        assert declared_evidence_statuses(notebook), notebook


def test_every_canonical_notebook_declares_reproducible_molab_bootstrap():
    snapshot = "0ac3efc5133fa6481519a2a373134c9e6f50689c"
    source_hash = "1a769bbbbb2fa4451d4309248349799ce8ab5efc21e053e2bb3aa28ddcb53d83"
    for notebook in NOTEBOOKS:
        source = notebook.read_text(encoding="utf-8")
        assert source.startswith("# /// script"), notebook
        assert f"desafio-01/archive/{{snapshot}}.zip" in source, notebook
        assert snapshot in source, notebook
        assert source_hash in source, notebook
        assert "observed_source != expected_source" in source, notebook


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


def test_static_html_has_portuguese_reader_metadata():
    for notebook in NOTEBOOKS:
        html = (HTML_DIR / f"{notebook.stem}.html").read_text(encoding="utf-8")
        title, description = NOTEBOOK_METADATA[notebook.stem]
        assert '<html lang="pt-BR">' in html
        assert f"<title>{title}</title>" in html
        assert f'content="{description}"' in html
