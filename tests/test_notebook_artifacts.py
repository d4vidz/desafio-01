import hashlib
import json

import scripts.render_notebooks as render_notebooks
from scripts.render_notebooks import (
    HTML_DIR,
    MANIFEST_PATH,
    NOTEBOOKS,
    NOTEBOOK_METADATA,
    build_manifest,
    declared_evidence_statuses,
    source_digest,
)
from scripts.update_molab_context import SNAPSHOT_PATTERN


def test_every_canonical_notebook_declares_evidence_maturity():
    for notebook in NOTEBOOKS:
        assert declared_evidence_statuses(notebook), notebook


def test_every_canonical_notebook_declares_reproducible_molab_bootstrap():
    source_hash = "1a769bbbbb2fa4451d4309248349799ce8ab5efc21e053e2bb3aa28ddcb53d83"
    snapshots = set()
    for notebook in NOTEBOOKS:
        source = notebook.read_text(encoding="utf-8")
        assert source.startswith("# /// script"), notebook
        matches = SNAPSHOT_PATTERN.findall(source)
        assert len(matches) == 1, notebook
        snapshots.add(matches[0][1])
        assert "desafio-01/archive/{snapshot}.zip" in source, notebook
        assert source_hash in source, notebook
        assert "observed_source != expected_source" in source, notebook
    assert len(snapshots) == 1


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


def test_notebook_source_digest_is_stable_across_line_endings(tmp_path):
    notebook = tmp_path / "notebook.py"
    notebook.write_bytes(b"first\r\nsecond\r\n")
    expected = hashlib.sha256(b"first\nsecond\n").hexdigest()
    assert source_digest(notebook) == expected


def test_manifest_artifact_provenance_is_stable_across_line_endings(monkeypatch, tmp_path):
    notebook = tmp_path / "notebook.py"
    notebook.write_text(
        'EvidenceStatus.INFRASTRUCTURE\n__generated_with = "0.24.0"\n',
        encoding="utf-8",
    )
    source = tmp_path / "source.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    lock = tmp_path / "uv.lock"
    lock.write_text("lock\n", encoding="utf-8")
    html_directory = tmp_path / "html"
    html_directory.mkdir()
    html = html_directory / "notebook.html"
    html.write_bytes(b"<p>first</p>\r\n<p>second</p>\r\n")
    canonical = b"<p>first</p>\n<p>second</p>\n"

    monkeypatch.setattr(render_notebooks, "ROOT", tmp_path)
    monkeypatch.setattr(render_notebooks, "NOTEBOOKS", (notebook,))
    monkeypatch.setattr(render_notebooks, "SOURCE_PATH", source)
    monkeypatch.setattr(render_notebooks, "LOCK_PATH", lock)
    monkeypatch.setattr(
        render_notebooks,
        "NOTEBOOK_METADATA",
        {"notebook": ("Notebook", "Description")},
    )

    entry = render_notebooks.build_manifest(html_directory)["notebooks"][0]
    assert entry["html_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert entry["html_bytes"] == len(canonical)
