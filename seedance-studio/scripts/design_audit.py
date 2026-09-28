#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path

from knowledge_html import visible_text


GALLERY_ASSETS = [
    "assets/hero-command-center.png",
    "assets/hero-global-filmmaker-mode.png",
    "assets/infographic-skill-capabilities.png",
    "assets/infographic-cdn-delivery-map.png",
    "assets/infographic-reference-role-map.png",
    "assets/infographic-production-delivery.png",
    "assets/infographic-professional-qc-stack.png",
]

CORE_BITMAP_ASSETS = [
    *GALLERY_ASSETS,
    "assets/hero-cinematic.png",
    "assets/skill-os-infographic.png",
    "assets/skill-map-cinematic.png",
]


def png_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def check_png_asset(
    root: Path,
    rel: str,
    label: str,
    errors: list[str],
    *,
    min_bytes: int = 100_000,
    min_width: int = 1200,
    min_height: int = 650,
) -> None:
    path = root / rel
    if not path.exists():
        errors.append(f"missing asset: {rel}")
        return
    if path.stat().st_size < min_bytes:
        errors.append(f"{rel} appears too small for a real {label} image")
    size = png_dimensions(path)
    if size is None:
        errors.append(f"{rel} is not a valid PNG")
        return
    width, height = size
    if width < min_width or height < min_height:
        errors.append(f"{rel} is too small for README display ({width}x{height})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    errors = []

    readme = root / "README.md"
    if not readme.exists():
        errors.append("README.md missing")
    else:
        text = readme.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) < 80:
            errors.append(f"README.md is too short or collapsed ({len(lines)} lines)")
        long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 500]
        if long_lines:
            errors.append("README.md has lines over 500 chars: " + ", ".join(map(str, long_lines[:10])))
        for required in [
            "assets/hero-command-center.png",
            "assets/hero-global-filmmaker-mode.png",
            "assets/skill-os-infographic.png",
            "assets/skill-map-cinematic.png",
            "# Seedance Studio",
            "## v7.0.0 Breaking Change",
            "v7.3.0",
            "## Capability Map",
            "## Native Language Notes",
            "## Reference Assets",
            "## Longer Stories",
            "## Validation",
            "assets/hero-dark.svg",
            "assets/hero-light.svg",
            "assets/skill-map.svg",
        ]:
            if required not in text:
                errors.append(f"README.md missing `{required}`")
        gallery_count = sum(1 for rel in GALLERY_ASSETS if rel in text)
        if gallery_count < 6:
            errors.append(f"README.md must reference at least six visual-gallery PNG assets ({gallery_count} found)")
        for rel in GALLERY_ASSETS:
            if rel not in text:
                errors.append(f"README.md missing gallery asset `{rel}`")

    design_reference = root / "references" / "frontend-design-system.html"
    if not design_reference.exists():
        errors.append("registered frontend-design-system.html missing")
    else:
        design_text = visible_text(design_reference).lower()
        if "text-rich infographics" not in design_text or "reject garbled" not in design_text:
            errors.append("frontend-design-system.html missing text-rich infographic quality rules")

    for rel in CORE_BITMAP_ASSETS:
        check_png_asset(root, rel, "README visual", errors)

    for rel in ["assets/hero-dark.svg", "assets/hero-light.svg", "assets/skill-map.svg"]:
        path = root / rel
        if not path.exists():
            errors.append(f"missing asset: {rel}")
            continue
        svg = path.read_text(encoding="utf-8", errors="ignore")
        if "<svg" not in svg:
            errors.append(f"{rel} is not an SVG")
        if "<title>" not in svg or "<desc>" not in svg:
            errors.append(f"{rel} missing accessible title/desc")
        if re.search(r"<script|href=[\"\']https?://|xlink:href=[\"\']https?://", svg, re.I):
            errors.append(f"{rel} must not include scripts or external resources")
        if "linearGradient" in svg or "feGaussianBlur" in svg:
            errors.append(f"{rel} must follow the editorial standard: no gradients or blur filters")
        if "Georgia" not in svg or "ui-monospace" not in svg:
            errors.append(f"{rel} missing the editorial serif/monospace type stacks")

    if errors:
        print("Design audit errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Design audit passed: README and visual assets are structured and accessible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
