"""Tests for the HACS release archive."""

from pathlib import Path
from zipfile import ZipFile

from scripts.build_release_archive import build_archive


def test_build_archive_has_hacs_layout(tmp_path: Path) -> None:
    """Archive files are rooted correctly and omit Python caches."""
    source_dir = tmp_path / "custom_components" / "roth_touchline"
    source_dir.mkdir(parents=True)
    (source_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (source_dir / "sensor.py").write_text("", encoding="utf-8")
    cache_dir = source_dir / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "sensor.pyc").write_bytes(b"cache")
    output_path = tmp_path / "roth_touchline.zip"

    build_archive(source_dir, output_path)

    with ZipFile(output_path) as archive:
        assert archive.namelist() == ["manifest.json", "sensor.py"]
