#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from knowledge_html import load_knowledge_map, validate_registered_html

EXPECTED_SKILL_NAME = "seedance-studio"
EXPECTED_VERSION = "7.3.0"

FORBIDDEN_DIRECTORIES = ["skills", "docs"]

REQUIRED_FILES = [
    "README.md",
    "SKILL.md",
    "CHANGELOG.md",
    "V6_SEQUENCE_PROMPT_COMPILER_MANIFEST.md",
    "scripts/validate_skills.py",
    "scripts/content_audit.py",
    "scripts/eval_schema_check.py",
    "scripts/design_audit.py",
    "scripts/install_codex_skill.py",
    "scripts/source_registry_check.py",
    "scripts/vocab_schema_check.py",
    "scripts/prompt_lint.py",
    "scripts/project_state_check.py",
    "scripts/continuity_chain_check.py",
    "scripts/behavior_contract_check.py",
    "scripts/sequence_eval_check.py",
    "scripts/generation_run_check.py",
    "scripts/knowledge_html.py",
    ".github/workflows/validate-skills.yml",
    "agents/openai.yaml",
    "evals/evals.json",
    "evals/generation-benchmark.json",
    "data/sources.seedance-2026-05-30.json",
    "data/community-patterns.seedance-2026-05-30.json",
    "data/generation-runs.example.jsonl",
    "data/knowledge-map.json",
    "assets/knowledge-base.css",
    "references/index.html",
    "references/operating-loop.html",
    "schemas/project-state.schema.json",
    "schemas/clip-contract.schema.json",
    "schemas/take-review.schema.json",
    "schemas/prompt-spec.schema.json",
    "schemas/generation-run.schema.json",
    "examples/sequence-airport-arrival/project-state.json",
    "examples/sequence-airport-arrival/sequence-plan.md",
    "examples/sequence-airport-arrival/clip-01-contract.json",
    "examples/sequence-airport-arrival/clip-01-prompt.md",
    "examples/sequence-airport-arrival/clip-01-take-review.json",
    "examples/sequence-airport-arrival/clip-02-continuation-contract.json",
    "examples/sequence-airport-arrival/clip-02-prompt.md",
    "examples/sequence-observed-deviation/project-state-before.json",
    "examples/sequence-observed-deviation/take-review.json",
    "examples/sequence-observed-deviation/project-state-after.json",
    "examples/standalone-clip/project-state.json",
    "examples/standalone-clip/prompt.md",
    "examples/golden-prompts/compact-i2v.md",
    "examples/golden-prompts/r2v-role-isolation.md",
    "examples/golden-prompts/phased-single-take.md",
    "examples/golden-prompts/dense-2d-storyboard.md",
    "examples/golden-prompts/sequence-continuation.md",
    "examples/golden-prompts/continuation-observed-deviation.md",
    "examples/golden-prompts/first-last-frame-transition.md",
    "examples/golden-prompts/video-edit-one-layer.md",
    "examples/golden-prompts/storyboard-reference-workflow.md",
    "assets/hero-command-center.png",
    "assets/hero-global-filmmaker-mode.png",
    "assets/infographic-skill-capabilities.png",
    "assets/infographic-cdn-delivery-map.png",
    "assets/infographic-reference-role-map.png",
    "assets/infographic-production-delivery.png",
    "assets/infographic-professional-qc-stack.png",
    "assets/hero-cinematic.png",
    "assets/skill-os-infographic.png",
    "assets/skill-map-cinematic.png",
    "assets/hero-dark.svg",
    "assets/hero-light.svg",
    "assets/skill-map.svg",
]

REQUIRED_FIELDS = ["name", "description", "license", "metadata"]

REQUIRED_ROOT_MARKERS = [
    "## Root Operating Loop",
    "## Knowledge surface",
    "## Version and claim boundary",
    "## Validation contract",
    "single-entrypoint",
    "mandatory gates",
    "Sequence invariants",
    "observed_end_state",
    "data/knowledge-map.json",
]

EXPECTED_CAPABILITIES = [
    "seedance-interview",
    "seedance-interview-short",
    "seedance-sequence",
    "seedance-continuation",
    "seedance-prompt",
    "seedance-prompt-short",
    "seedance-camera",
    "seedance-motion",
    "seedance-lighting",
    "seedance-characters",
    "seedance-style",
    "seedance-vfx",
    "seedance-audio",
    "seedance-pipeline",
    "seedance-recipes",
    "seedance-troubleshoot",
    "seedance-copyright",
    "seedance-antislop",
    "seedance-filter",
    "seedance-vocab-en",
    "seedance-vocab-zh",
    "seedance-vocab-ja",
    "seedance-vocab-ko",
    "seedance-vocab-es",
    "seedance-vocab-ru",
    "seedance-examples-zh",
    "seedance-examples-ja",
    "seedance-examples-ko",
]


def split_frontmatter(text: str) -> tuple[str, str]:
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter must start with a standalone --- line")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("frontmatter must end with a standalone --- line") from exc
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:])


def top_keys(frontmatter: str) -> list[str]:
    keys = []
    for line in frontmatter.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    return keys


def value_for(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.*)$", frontmatter, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
        value = value[1:-1]
    return value


def metadata_value(frontmatter: str, key: str) -> str | None:
    in_metadata = False
    for line in frontmatter.splitlines():
        if line.startswith("metadata:"):
            in_metadata = True
            continue
        if in_metadata and line and not line.startswith(" "):
            break
        if in_metadata:
            match = re.match(rf"^\s+{re.escape(key)}:\s*(.*)$", line)
            if match:
                value = match.group(1).strip()
                if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
                    value = value[1:-1]
                return value
    return None


def validate_skill(path: Path, root: Path, errors: list[str], warnings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    try:
        frontmatter, body = split_frontmatter(text)
    except Exception as exc:
        errors.append(f"{rel}: {exc}")
        return

    keys = top_keys(frontmatter)
    for field in REQUIRED_FIELDS:
        if field not in keys:
            errors.append(f"{rel}: missing top-level field `{field}`")

    if value_for(frontmatter, "name") != EXPECTED_SKILL_NAME:
        errors.append(f"{rel}: name must be `{EXPECTED_SKILL_NAME}`")
    if metadata_value(frontmatter, "version") != EXPECTED_VERSION:
        errors.append(f"{rel}: metadata.version must be {EXPECTED_VERSION}")
    if metadata_value(frontmatter, "user-invocable") != "true":
        errors.append(f"{rel}: metadata.user-invocable must be true")
    if metadata_value(frontmatter, "tags") is None:
        errors.append(f"{rel}: metadata.tags is required")

    description = value_for(frontmatter, "description") or ""
    if not description.startswith("This skill should be used when"):
        errors.append(f"{rel}: description must use third-person activation wording")

    if len(body.splitlines()) < 35:
        errors.append(f"{rel}: short entrypoint is unexpectedly short")

    for marker in REQUIRED_ROOT_MARKERS:
        if marker not in body:
            errors.append(f"{rel}: missing entrypoint marker `{marker}`")

    forbidden_contracts = [
        "[skill:seedance-",
        "$seedance-2-integrated-workflow",
        "metadata.parent: \"seedance-studio\"",
    ]
    for marker in forbidden_contracts:
        if marker in text:
            errors.append(f"{rel}: contains legacy contract marker `{marker}`")
    if "single-file" in text.lower():
        errors.append(f"{rel}: single-file wording remains after HTML migration")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if root.name != EXPECTED_SKILL_NAME:
        errors.append(f"repository directory must be `{EXPECTED_SKILL_NAME}`")

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")

    for rel in FORBIDDEN_DIRECTORIES:
        if (root / rel).exists():
            errors.append(f"legacy directory must be removed: {rel}")

    validate_skill(root / "SKILL.md", root, errors, warnings)

    html_errors = validate_registered_html(root)
    errors.extend(html_errors)
    knowledge_map, map_errors = load_knowledge_map(root)
    errors.extend(map_errors)
    topics = knowledge_map.get("topics", []) if isinstance(knowledge_map, dict) else []
    capabilities = {
        topic.get("id", ""): topic
        for topic in topics
        if isinstance(topic, dict) and str(topic.get("id", "")).startswith("capability-")
    }
    expected_ids = {f"capability-{name}" for name in EXPECTED_CAPABILITIES}
    if set(capabilities) != expected_ids:
        errors.append("knowledge map must register all 28 capabilities exactly once")
    for capability in expected_ids:
        topic = capabilities.get(capability)
        if topic and topic.get("path") != f"references/capabilities/{capability.removeprefix('capability-')}.html":
            errors.append(f"knowledge map capability path mismatch: {capability}")

    pycache = root / "scripts" / "__pycache__"
    if pycache.exists():
        errors.append("scripts/__pycache__ must not be committed")
    for pyc in root.rglob("*.pyc"):
        rel = pyc.relative_to(root).as_posix()
        if not rel.startswith(".seedance_backups/"):
            errors.append(f"compiled Python cache must not be committed: {rel}")

    eval_path = root / "evals" / "evals.json"
    if eval_path.exists():
        try:
            data = json.loads(eval_path.read_text(encoding="utf-8"))
            cases = data.get("cases", [])
            if len(cases) < 16:
                errors.append("evals/evals.json must contain at least 16 cases")
        except Exception as exc:
            errors.append(f"evals/evals.json parse error: {exc}")

    installer = root / "scripts" / "install_codex_skill.py"
    if installer.exists():
        installer_text = installer.read_text(encoding="utf-8")
        if 'SKILL_NAME = "seedance-studio"' not in installer_text:
            errors.append("scripts/install_codex_skill.py must install seedance-studio")

    openai_yaml = root / "agents" / "openai.yaml"
    if openai_yaml.exists():
        yaml_text = openai_yaml.read_text(encoding="utf-8")
        for required in [
            'display_name: "Seedance Studio"',
            'short_description: "Single-skill Seedance video studio"',
            'default_prompt: "Use $<seedance-studio>',
            "allow_implicit_invocation: true",
        ]:
            if required not in yaml_text:
                errors.append(f"agents/openai.yaml missing `{required}`")

    readme = root / "README.md"
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
        for required in ("$<seedance-studio>", "/seedance-studio"):
            if required not in readme_text:
                errors.append(f"README.md must document `{required}` invocation")

    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"- {warning}")
        print()

    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {EXPECTED_SKILL_NAME} single-entrypoint package v{EXPECTED_VERSION} with registered HTML knowledge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
