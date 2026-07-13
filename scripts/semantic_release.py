"""Calculate and apply the next semantic version for a merged change."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

SEMVER_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\." + r"(?P<minor>0|[1-9]\d*)\." + r"(?P<patch>0|[1-9]\d*)$"
)
CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r"^(?P<type>build|chore|ci|docs|feat|fix|perf|refactor|revert|test)"
    + r"(?:\([a-z0-9._-]+\))?(?P<breaking>!)?: .+",
    re.MULTILINE,
)
BREAKING_CHANGE_PATTERN = re.compile(r"^BREAKING CHANGE:", re.MULTILINE)


def next_version(current_version: str, change_description: str) -> str:
    """Return the next semantic version for a merged change."""
    version_match = SEMVER_PATTERN.fullmatch(current_version)
    if version_match is None:
        raise ValueError(f"Invalid semantic version: {current_version}")

    major, minor, patch = (
        int(version_match.group(part)) for part in ("major", "minor", "patch")
    )
    change_match = CONVENTIONAL_COMMIT_PATTERN.search(change_description)

    if (
        change_match is not None and change_match.group("breaking") is not None
    ) or BREAKING_CHANGE_PATTERN.search(change_description):
        return f"{major + 1}.0.0"
    if change_match is not None and change_match.group("type") == "feat":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def update_manifest(manifest_path: Path, change_description: str) -> str:
    """Update a Home Assistant manifest and return its new version."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = next_version(manifest["version"], change_description)
    manifest["version"] = version
    manifest_path.write_text(
        f"{json.dumps(manifest, indent=2, ensure_ascii=False)}\n",
        encoding="utf-8",
    )
    return version


def main() -> None:
    """Update the manifest version from command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    change_source = parser.add_mutually_exclusive_group(required=True)
    change_source.add_argument("--change")
    change_source.add_argument("--change-file", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    change_description = (
        args.change_file.read_text(encoding="utf-8")
        if args.change_file is not None
        else args.change
    )
    version = update_manifest(args.manifest, change_description)
    print(version)
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as github_output:
            github_output.write(f"version={version}\n")


if __name__ == "__main__":
    main()
