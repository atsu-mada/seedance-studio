#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from urllib.parse import urlparse


REQUIRED_RUN_FIELDS = {
    "run_id", "project_id", "clip_id", "surface", "prompt_version",
    "input_mode", "reference_tags", "prompt", "result_status", "is_synthetic_fixture",
}
REQUIRED_BENCHMARK_FIELDS = {
    "benchmark_version", "updated", "cases",
}
RESULT_STATUSES = {"not_run_fixture", "submitted", "generated", "reviewed", "accepted", "rejected"}
PROVIDER_STATUSES = {"unknown", "queued", "processing", "completed", "failed"}
TECHNICAL_QC_STATUSES = {"not_checked", "pass", "fail"}
PERCEPTUAL_REVIEW_STATUSES = {"pending", "pass", "fail", "uncertain"}
OPTIONAL_EVIDENCE_FIELDS = {
    "provider_status", "technical_qc", "perceptual_review", "review_evidence",
}
REQUIRED_STRING_FIELDS = {
    "run_id", "project_id", "clip_id", "surface", "prompt_version", "input_mode", "prompt",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_review_path(value: str, root: Path | None, label: str) -> list[str]:
    errors: list[str] = []
    if not value or not value.strip():
        return [f"{label}: review_evidence path must not be empty"]
    if "\x00" in value:
        return [f"{label}: review_evidence path contains a NUL byte"]
    normalized = value.replace("\\", "/")
    if any(part == ".." for part in normalized.split("/")):
        errors.append(f"{label}: review_evidence path must not contain traversal: {value}")
        return errors
    try:
        parsed = urlparse(value)
    except ValueError:
        return [f"{label}: review_evidence path is not a valid relative path: {value}"]
    if parsed.scheme or parsed.netloc:
        errors.append(f"{label}: review_evidence path must be project-relative, not a URL: {value}")
        return errors
    if parsed.query or parsed.fragment:
        errors.append(f"{label}: review_evidence path must not contain a query or fragment: {value}")
        return errors
    if Path(normalized).is_absolute() or PureWindowsPath(value).is_absolute() or PureWindowsPath(value).drive:
        errors.append(f"{label}: review_evidence path must not be absolute: {value}")
        return errors
    if value in {".", "./"}:
        errors.append(f"{label}: review_evidence path must name a project-relative file: {value}")
        return errors
    if root is not None:
        try:
            root_path = root.resolve()
            candidate = (root_path / normalized).resolve()
            candidate.relative_to(root_path)
        except (OSError, RuntimeError, ValueError):
            errors.append(f"{label}: review_evidence path escapes project root: {value}")
    return errors


def validate_run_record(record: object, *, root: Path | None = None, label: str = "record") -> list[str]:
    """Validate one legacy-compatible generation-run record without mutating it."""
    if not isinstance(record, dict):
        return [f"{label}: record must be an object"]

    errors: list[str] = []
    missing = REQUIRED_RUN_FIELDS - set(record)
    if missing:
        errors.append(f"{label}: missing {', '.join(sorted(missing))}")

    for field in sorted(REQUIRED_STRING_FIELDS):
        if field in record and not isinstance(record[field], str):
            errors.append(f"{label}: {field} must be a string")
    if "reference_tags" in record:
        tags = record["reference_tags"]
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            errors.append(f"{label}: reference_tags must be a list of strings")
    if "is_synthetic_fixture" in record and not isinstance(record["is_synthetic_fixture"], bool):
        errors.append(f"{label}: is_synthetic_fixture must be a boolean")

    result_status = record.get("result_status")
    if not isinstance(result_status, str) or result_status not in RESULT_STATUSES:
        errors.append(f"{label}: result_status must be one of {sorted(RESULT_STATUSES)}")

    provider_status = record.get("provider_status")
    if "provider_status" in record and (
        not isinstance(provider_status, str) or provider_status not in PROVIDER_STATUSES
    ):
        errors.append(f"{label}: provider_status must be one of {sorted(PROVIDER_STATUSES)}")
    technical_qc = record.get("technical_qc")
    if "technical_qc" in record and (
        not isinstance(technical_qc, str) or technical_qc not in TECHNICAL_QC_STATUSES
    ):
        errors.append(f"{label}: technical_qc must be one of {sorted(TECHNICAL_QC_STATUSES)}")
    perceptual_review = record.get("perceptual_review")
    if "perceptual_review" in record and (
        not isinstance(perceptual_review, str) or perceptual_review not in PERCEPTUAL_REVIEW_STATUSES
    ):
        errors.append(f"{label}: perceptual_review must be one of {sorted(PERCEPTUAL_REVIEW_STATUSES)}")

    evidence = record.get("review_evidence")
    if "review_evidence" in record:
        if not isinstance(evidence, list):
            errors.append(f"{label}: review_evidence must be a list of project-relative paths")
        else:
            for index, path in enumerate(evidence):
                if not isinstance(path, str):
                    errors.append(f"{label}: review_evidence[{index}] must be a string path")
                    continue
                errors.extend(_validate_review_path(path, root, f"{label}: review_evidence[{index}]"))

    if record.get("is_synthetic_fixture") is True and result_status != "not_run_fixture":
        errors.append(f"{label}: fixture must not pretend to be production result")

    if isinstance(result_status, str) and result_status in RESULT_STATUSES:
        if isinstance(provider_status, str) and provider_status in PROVIDER_STATUSES:
            if provider_status in {"queued", "processing"} and result_status != "submitted":
                errors.append(f"{label}: provider_status {provider_status} requires result_status submitted")
            elif provider_status == "completed" and result_status == "submitted":
                errors.append(f"{label}: result_status submitted contradicts provider_status completed")
            elif provider_status == "failed" and result_status != "rejected":
                errors.append(f"{label}: provider_status failed requires result_status rejected")
            if result_status == "not_run_fixture" and provider_status != "unknown":
                errors.append(f"{label}: not_run_fixture cannot carry provider_status {provider_status}")

        if result_status == "accepted" and OPTIONAL_EVIDENCE_FIELDS.intersection(record):
            required_approval = {
                "provider_status": "completed",
                "technical_qc": "pass",
                "perceptual_review": "pass",
            }
            for field, expected in required_approval.items():
                if record.get(field) != expected:
                    errors.append(f"{label}: accepted record with evidence fields requires {field}={expected}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo).resolve()
    errors: list[str] = []

    benchmark = root / "evals" / "generation-benchmark.json"
    if not benchmark.exists():
        errors.append("missing evals/generation-benchmark.json")
    else:
        try:
            data = load_json(benchmark)
        except Exception as exc:
            errors.append(f"evals/generation-benchmark.json invalid JSON: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("generation benchmark must be object")
            else:
                missing = REQUIRED_BENCHMARK_FIELDS - set(data)
                if missing:
                    errors.append("generation benchmark missing: " + ", ".join(sorted(missing)))
                cases = data.get("cases")
                if not isinstance(cases, list) or len(cases) < 3:
                    errors.append("generation benchmark needs at least three cases")

    runs = root / "data" / "generation-runs.example.jsonl"
    if not runs.exists():
        errors.append("missing data/generation-runs.example.jsonl")
    else:
        count = 0
        for lineno, line in enumerate(runs.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            count += 1
            try:
                record = json.loads(line)
            except Exception as exc:
                errors.append(f"generation-runs.example.jsonl:{lineno}: invalid JSONL: {exc}")
                continue
            errors.extend(
                validate_run_record(
                    record,
                    root=root,
                    label=f"generation-runs.example.jsonl:{lineno}",
                )
            )
        if count < 2:
            errors.append("generation-runs.example.jsonl needs at least two records")

    if errors:
        print("Generation run errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Generation run check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
