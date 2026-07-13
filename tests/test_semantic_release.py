"""Tests for automatic semantic version releases."""

import json
from pathlib import Path

import pytest

from scripts.semantic_release import main, next_version, update_manifest


@pytest.mark.parametrize(
    ("change_description", "expected"),
    [
        ("fix: handle controller timeout", "1.2.4"),
        ("perf(parser): reduce allocations", "1.2.4"),
        ("docs: explain setup", "1.2.4"),
        ("Merge pull request #10\n\nfeat: discover zones", "1.3.0"),
        ("feat!: replace configuration format", "2.0.0"),
        ("fix: adjust parsing\n\nBREAKING CHANGE: remove legacy XML", "2.0.0"),
    ],
)
def test_next_version(change_description: str, expected: str) -> None:
    """Change descriptions select the expected semantic version bump."""
    assert next_version("1.2.3", change_description) == expected


def test_invalid_current_version() -> None:
    """A non-semantic current version is rejected."""
    with pytest.raises(ValueError, match="Invalid semantic version"):
        next_version("v1.2", "fix: test")


def test_update_manifest(tmp_path: Path) -> None:
    """Updating a manifest preserves its data and writes the new version."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"domain": "roth_touchline", "version": "1.0.0"}),
        encoding="utf-8",
    )

    assert update_manifest(manifest_path, "feat: add control") == "1.1.0"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == {
        "domain": "roth_touchline",
        "version": "1.1.0",
    }


def test_main_reads_change_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The workflow can safely pass pull request text through a file."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"version": "1.0.0"}', encoding="utf-8")
    change_path = tmp_path / "change.txt"
    change_path.write_text("feat: add control", encoding="utf-8")
    output_path = tmp_path / "github-output.txt"
    monkeypatch.setattr(
        "sys.argv",
        [
            "semantic_release.py",
            "--manifest",
            str(manifest_path),
            "--change-file",
            str(change_path),
            "--github-output",
            str(output_path),
        ],
    )

    main()

    assert capsys.readouterr().out == "1.1.0\n"
    assert output_path.read_text(encoding="utf-8") == "version=1.1.0\n"
