"""Build the HACS ZIP archive for a custom integration release."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build_archive(source_dir: Path, output_path: Path) -> None:
    """Write integration files to a HACS archive without a directory prefix."""
    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                archive.write(path, path.relative_to(source_dir))


def main() -> None:
    """Build an archive from command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build_archive(args.source, args.output)


if __name__ == "__main__":
    main()
