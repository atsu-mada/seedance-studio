#!/usr/bin/env python3
"""Legacy copy-only installer for the Seedance Studio skill.

This installer intentionally copies the package to a user-selected legacy
skills directory. It never deploys to the shared canonical skill location.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
from pathlib import Path


SKILL_NAME = "seedance-studio"
IGNORE_NAMES = {
    ".git",
    ".github",
    ".pytest_cache",
    ".seedance_backups",
    "__pycache__",
}
IGNORE_PATTERNS = ["*.pyc", "*.pyo", "*.tmp", "*.log", "*.psd"]


def default_skills_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def configured_canonical_root() -> Path | None:
    """Return the optional shared canonical root (AGENT_SKILLS_ROOT) that this installer must protect."""
    override = os.environ.get("AGENT_SKILLS_ROOT")
    if override:
        return Path(override).expanduser().resolve(strict=False)
    return None


def paths_overlap(left: Path, right: Path) -> bool:
    """Return whether either resolved path is an ancestor of the other."""
    return left == right or left in right.parents or right in left.parents


def ignore_runtime_noise(_src: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in IGNORE_NAMES:
            ignored.add(name)
            continue
        if any(fnmatch.fnmatch(name, pattern) for pattern in IGNORE_PATTERNS):
            ignored.add(name)
    return ignored


def payload_size(path: Path) -> str:
    total = float(sum(item.stat().st_size for item in path.rglob("*") if item.is_file()))
    for unit in ["B", "KB", "MB", "GB"]:
        if total < 1024 or unit == "GB":
            return f"{total:.1f} {unit}"
        total /= 1024
    return f"{total:.1f} GB"


def assert_safe_destination(
    destination: Path,
    skills_dir: Path,
    *,
    source_root: Path | None = None,
    canonical_root: Path | None = None,
) -> None:
    """Reject unsafe destinations before the installer can mutate anything."""
    if destination.is_symlink():
        raise ValueError(f"destination must not be a symlink: {destination}")
    if skills_dir.is_symlink():
        raise ValueError(f"skills directory must not be a symlink: {skills_dir}")

    resolved_destination = destination.resolve(strict=False)
    resolved_skills_dir = skills_dir.resolve(strict=False)
    if source_root is not None:
        resolved_source_root = source_root.expanduser().resolve(strict=False)
        if paths_overlap(resolved_source_root, resolved_destination):
            raise ValueError(
                "source and destination must not overlap: "
                f"source={resolved_source_root}, destination={resolved_destination}"
            )

    protected_root = canonical_root or configured_canonical_root()
    resolved_canonical_root = protected_root.expanduser().resolve(strict=False) if protected_root else None
    if resolved_canonical_root is not None and paths_overlap(resolved_canonical_root, resolved_destination):
        raise ValueError(
            "destination must not overlap the shared canonical skills directory: "
            f"{resolved_canonical_root}"
        )

    if resolved_destination.name != SKILL_NAME:
        raise ValueError(f"destination must end with {SKILL_NAME}: {resolved_destination}")
    if resolved_skills_dir not in resolved_destination.parents:
        raise ValueError(f"destination must stay inside the skills directory: {resolved_skills_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legacy copy-only install; shared canonical skill destinations are rejected."
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=default_skills_dir(),
        help=(
            "Legacy Codex skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills; "
            "the configured AGENT_SKILLS_ROOT canonical root is always rejected."
        ),
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing seedance-studio install.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source_skill = repo_root / "SKILL.md"
    if not source_skill.exists():
        raise FileNotFoundError(f"SKILL.md not found at {source_skill}")

    skills_dir = args.dest.expanduser()
    destination = skills_dir / SKILL_NAME
    assert_safe_destination(
        destination,
        skills_dir,
        source_root=repo_root,
        canonical_root=configured_canonical_root(),
    )

    skills_dir.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not args.force:
            print(f"{SKILL_NAME} is already installed at {destination}")
            print("Run again with --force to replace it.")
            return 1
        shutil.rmtree(destination)

    shutil.copytree(repo_root, destination, ignore=ignore_runtime_noise)

    print(f"Installed {SKILL_NAME} to {destination}")
    print(f"Installed payload size: {payload_size(destination)}")
    print("Restart Codex to pick up new skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
