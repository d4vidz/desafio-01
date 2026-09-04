import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "translation-pairs.json"
ISSUE_TEMPLATES = ROOT / ".gitlab" / "issue_templates"
MR_TEMPLATES = ROOT / ".gitlab" / "merge_request_templates"
sys.path.insert(0, str(ROOT))

from scripts.check_translation_pairs import check_manifest  # noqa: E402


def test_repository_translation_pairs_are_synchronized():
    assert check_manifest(ROOT, MANIFEST) == []


def test_required_gitlab_templates_have_acceptance_sections():
    for filename in (
        "pergunta_analitica.md",
        "especificacao.md",
        "entrega.md",
        "mudanca_ou_correcao.md",
    ):
        content = (ISSUE_TEMPLATES / filename).read_text(encoding="utf-8")
        assert "## Critérios de aceitação" in content

    merge_request = (MR_TEMPLATES / "analise.md").read_text(encoding="utf-8")
    assert "## Checklist" in merge_request


def test_checker_detects_a_stale_canonical_hash(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "pt.md").write_text("versão 1\n", encoding="utf-8")
    (tmp_path / "docs" / "en.md").write_text("version 1\n", encoding="utf-8")
    manifest = tmp_path / "docs" / "translation-pairs.json"
    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "pairs": [
                    {
                        "canonical": "docs/pt.md",
                        "translation": "docs/en.md",
                        "canonical_sha256": "0" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    errors = check_manifest(tmp_path, manifest)

    assert len(errors) == 1
    assert "canonical hash is stale" in errors[0]


def test_checker_rejects_paths_outside_repository(tmp_path):
    (tmp_path / "docs").mkdir()
    manifest = tmp_path / "docs" / "translation-pairs.json"
    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "pairs": [
                    {
                        "canonical": "../outside.md",
                        "translation": "docs/en.md",
                        "canonical_sha256": "0" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    errors = check_manifest(tmp_path, manifest)

    assert any("escapes repository root" in error for error in errors)
