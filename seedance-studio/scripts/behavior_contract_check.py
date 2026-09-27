#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_html import load_knowledge_map, visible_text


REQUIRED_SNIPPETS = [
    "Root Operating Loop",
    "Sequence Gate",
    "Capability section: seedance-sequence",
    "Capability section: seedance-continuation",
    "accepted observed state overrides planned state",
    "rejected footage",
    "exact reference tags",
    "Plan globally",
    "final outcome",
    "provisional intent cards",
    "Clip 01 final Seedance prompt",
    "Required Input Gate",
    "accepted previous clip or accepted final frame",
    "observed_end_state",
    "Do not hide this uncertainty",
    "natural-language Seedance prompt",
    "Do not emit internal JSON",
    "Do not replay completed actions",
    "Do not perform reserved later actions",
    "Do not hardcode duration",
    "conservative generic profile",
    "Storyboard Reference Workflow",
    "GridTileStyle",
    "storyboard controls rough blocking and camera flow only; do not transfer start frame, final visual style, lighting, character identity, costume, or environment detail.",
    "source-panel numbers and transition arrows",
    "candidate ID, batch ID, inputs, prompt version, dimensions, hash",
    "isolated",
    "pending_approval",
    "approved",
    "rejected",
    "explicit batch approval",
    "provenance or authorization is missing",
    "active references, canonical state, final prompts, and parent sources remain unchanged",
    "finished-look",
    "unwanted-text",
]

STORYBOARD_REQUIRED_SNIPPETS = [
    "storyboard controls rough blocking and camera flow only; do not transfer start frame, final visual style, lighting, character identity, costume, or environment detail.",
    "Canonical identity and accepted continuity state always override storyboard.",
    "explicit batch approval records approver, timestamp, and selected candidate IDs.",
    "Pending or rejected candidates cannot progress.",
    "If any required provenance or authorization is missing, stop before human approval.",
    "Source-panel numbers and transition arrows are planning annotations only and must not transfer to generated video.",
]

DOMAIN_MARKERS = [
    "seedance-camera",
    "seedance-motion",
    "seedance-characters",
    "seedance-audio",
    "seedance-lighting",
    "seedance-style",
    "seedance-recipes",
    "seedance-prompt-short",
    "seedance-troubleshoot",
]


def contract_errors(root: Path) -> list[str]:
    errors: list[str] = []

    skill_path = root / "SKILL.md"
    if not skill_path.exists():
        errors.append("missing SKILL.md")
        text = ""
    else:
        text = skill_path.read_text(encoding="utf-8")

    knowledge_map, map_errors = load_knowledge_map(root)
    errors.extend(map_errors)
    documents: dict[str, str] = {}
    for topic in knowledge_map.get("topics", []) if isinstance(knowledge_map, dict) else []:
        if not isinstance(topic, dict) or not isinstance(topic.get("path"), str):
            continue
        path = root / topic["path"]
        if path.exists():
            documents[topic["id"]] = visible_text(path)
    combined = "\n".join(documents.values()) + "\n" + text
    low = combined.lower()
    for snippet in REQUIRED_SNIPPETS:
        if snippet.lower() not in low:
            errors.append(f"registered HTML knowledge: missing behavior phrase `{snippet}`")

    for snippet in STORYBOARD_REQUIRED_SNIPPETS:
        if snippet.lower() not in low:
            errors.append(f"registered HTML knowledge: missing storyboard behavior phrase `{snippet}`")

    for marker in DOMAIN_MARKERS:
        topic_id = f"capability-{marker}"
        section = documents.get(topic_id, "")
        if not section:
            errors.append(f"registered HTML knowledge: missing domain document `{marker}`")
            continue
        window = section.lower()
        if "sequence state" not in window or "reserved" not in window or "continuity locks" not in window:
            errors.append(
                f"registered HTML knowledge: `{marker}` document must read sequence state, continuity locks, and reserved beats when present"
            )

    continuation = documents.get("capability-seedance-continuation", "").lower()
    for snippet in ("accepted previous clip or accepted final frame", "observed_end_state", "continuity locks"):
        if snippet.lower() not in continuation:
            errors.append(
                "registered HTML knowledge: capability-seedance-continuation missing gate phrase "
                f"`{snippet}`"
            )

    if "[skill:seedance-" in combined:
        errors.append("registered HTML knowledge: legacy sub-skill invocation marker remains")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    errors = contract_errors(Path(args.repo).resolve())

    if errors:
        print("Behavior contract errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Behavior contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
