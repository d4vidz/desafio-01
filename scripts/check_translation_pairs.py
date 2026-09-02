"""Check that registered translations exist and track the current canonical hash."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path("docs/translation-pairs.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_path(root: Path, relative: str, field: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} escapes repository root: {relative}") from exc
    return candidate


def check_manifest(root: Path = DEFAULT_ROOT, manifest: Path = DEFAULT_MANIFEST) -> list[str]:
    """Return validation errors; an empty list means the manifest is valid."""

    manifest_path = manifest if manifest.is_absolute() else root / manifest
    errors: list[str] = []
    try:
        payload: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"manifest not found: {manifest_path}"]
    except json.JSONDecodeError as exc:
        return [f"invalid JSON in {manifest_path}: {exc}"]

    pairs = payload.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        return ["manifest must contain a non-empty 'pairs' list"]

    seen_canonical: set[str] = set()
    for index, pair in enumerate(pairs):
        prefix = f"pairs[{index}]"
        if not isinstance(pair, dict):
            errors.append(f"{prefix} must be an object")
            continue
        canonical = pair.get("canonical")
        translation = pair.get("translation")
        expected_hash = pair.get("canonical_sha256")
        if not all(isinstance(value, str) and value for value in (canonical, translation, expected_hash)):
            errors.append(f"{prefix} requires non-empty canonical, translation, and canonical_sha256")
            continue
        if canonical in seen_canonical:
            errors.append(f"{prefix} duplicates canonical path: {canonical}")
        seen_canonical.add(canonical)
        try:
            canonical_path = _safe_path(root, canonical, f"{prefix}.canonical")
            translation_path = _safe_path(root, translation, f"{prefix}.translation")
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not canonical_path.is_file():
            errors.append(f"{prefix} canonical file not found: {canonical}")
            continue
        if not translation_path.is_file():
            errors.append(f"{prefix} translation file not found: {translation}")
        actual_hash = _sha256(canonical_path)
        if expected_hash != actual_hash:
            errors.append(
                f"{prefix} canonical hash is stale for {canonical}: "
                f"expected {expected_hash}, actual {actual_hash}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    errors = check_manifest(args.root.resolve(), args.manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Translation pairs are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
