#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from knowledge_html import html_table_rows, load_knowledge_map, visible_text

LANGS = ["en", "zh", "ru", "ja", "ko", "es"]
ALLOWED_FUNCTIONS = {
    "Role", "FirstLastFrame", "Camera", "Shot", "Lens", "Lighting", "Motion",
    "VFX", "Audio", "Text", "Editing", "Constraint", "Constraints", "Safety",
}
STRICT_REQUIRED_FUNCTIONS = {"Role", "FirstLastFrame", "Camera", "Audio", "Text", "Editing", "Constraint", "Safety"}
PROTECTED_TERMS = ["Studio Ghibli", "Ghibli", "Spider-Man", "Disney", "Marvel"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    errors: list[str] = []

    knowledge_map, map_errors = load_knowledge_map(root)
    errors.extend(map_errors)

    for lang in LANGS:
        rel = f"references/vocab/{lang}.html"
        path = root / rel
        if not path.exists():
            errors.append(f"missing registered vocab document: {rel}")
            continue
        text = visible_text(path)
        all_rows = html_table_rows(path)
        rows = [row for row in all_rows if len(row) >= 3 and row[0] != "Function"]

        if "Keep reference tags unchanged" not in text and "reference tags unchanged" not in text:
            errors.append(f"{rel}: missing reference-tag preservation note")
        if not any(row and row[0] == "Function" for row in all_rows):
            errors.append(f"{rel}: missing Function vocabulary table")
        html_source = path.read_text(encoding="utf-8")
        if not re.search(r'<h[1-6][^>]+id="slop-traps"[^>]*>Slop Traps</h[1-6]>', html_source):
            errors.append(f"{rel}: missing Slop Traps section (language-specific empty-quality words)")

        min_rows = 40
        if args.strict and len(rows) < min_rows:
            errors.append(f"{rel}: expected at least {min_rows} rows, found {len(rows)}")

        functions = set()
        for i, row in enumerate(rows, start=1):
            function, term, meaning = row[0], row[1], row[2]
            functions.add(function)
            if function not in ALLOWED_FUNCTIONS:
                errors.append(f"{rel}: row {i} has unsupported function `{function}`")
            if not function or not term or not meaning:
                errors.append(f"{rel}: row {i} has an empty cell")

        if args.strict:
            missing = STRICT_REQUIRED_FUNCTIONS - functions
            if missing:
                errors.append(f"{rel}: missing strict functions " + ", ".join(sorted(missing)))

        for protected in PROTECTED_TERMS:
            if protected in text:
                errors.append(f"{rel}: protected term `{protected}` should not appear in active vocab")

        if not re.search(r"\[Image1\].*\[Video1\]|\[Image1\].*\[Audio1\]", text, re.S):
            errors.append(f"{rel}: expected unchanged reference tag examples")

    if errors:
        print("Vocab schema errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Vocab schema check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
