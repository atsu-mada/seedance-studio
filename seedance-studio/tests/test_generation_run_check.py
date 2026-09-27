from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generation_run_check import validate_run_record  # noqa: E402


class GenerationRunTests(unittest.TestCase):
    def record(self, **overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "run_id": "run-01",
            "project_id": "project-01",
            "clip_id": "clip-01",
            "surface": "unknown_conservative",
            "prompt_version": "7.2.0",
            "input_mode": "I2V",
            "reference_tags": ["[Image1]"],
            "prompt": "A short synthetic test prompt.",
            "result_status": "generated",
            "is_synthetic_fixture": False,
        }
        record.update(overrides)
        return record

    def test_generation_run_fixtures_validate(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/generation_run_check.py", "--strict"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_accepted_record_remains_valid_without_optional_fields(self) -> None:
        record = self.record(result_status="accepted")
        before = dict(record)
        self.assertEqual(validate_run_record(record), [])
        self.assertEqual(record, before)
        self.assertTrue({
            "provider_status", "technical_qc", "perceptual_review", "review_evidence",
        }.isdisjoint(record))

    def test_submitted_processing_pair_is_valid_without_filling_other_fields(self) -> None:
        record = self.record(result_status="submitted", provider_status="processing")
        before = dict(record)
        self.assertEqual(validate_run_record(record), [])
        self.assertEqual(record, before)
        self.assertNotIn("technical_qc", record)
        self.assertNotIn("perceptual_review", record)
        self.assertNotIn("review_evidence", record)

    def test_accepted_evidence_requires_completed_qc_and_review(self) -> None:
        incomplete = self.record(result_status="accepted", provider_status="completed")
        errors = validate_run_record(incomplete)
        self.assertTrue(any("technical_qc=pass" in error for error in errors), errors)
        self.assertTrue(any("perceptual_review=pass" in error for error in errors), errors)

        complete = self.record(
            result_status="accepted",
            provider_status="completed",
            technical_qc="pass",
            perceptual_review="pass",
            review_evidence=["reviews/clip-01.json"],
        )
        self.assertEqual(validate_run_record(complete), [])

        for field, value in (
            ("provider_status", "queued"),
            ("provider_status", "processing"),
            ("provider_status", "failed"),
            ("technical_qc", "fail"),
            ("perceptual_review", "uncertain"),
        ):
            candidate = self.record(
                result_status="accepted",
                provider_status="completed",
                technical_qc="pass",
                perceptual_review="pass",
            )
            candidate[field] = value
            self.assertTrue(validate_run_record(candidate), (field, value))

    def test_provider_and_result_status_contradictions_fail(self) -> None:
        cases = (
            {"result_status": "generated", "provider_status": "processing"},
            {"result_status": "submitted", "provider_status": "completed"},
            {"result_status": "generated", "provider_status": "failed"},
            {"result_status": "not_run_fixture", "provider_status": "completed"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.assertTrue(validate_run_record(self.record(**overrides)))

    def test_optional_fields_reject_null_list_and_unknown_values(self) -> None:
        for field in ("provider_status", "technical_qc", "perceptual_review"):
            for value in (None, [], {}, "invalid"):
                with self.subTest(field=field, value=value):
                    errors = validate_run_record(self.record(**{field: value}))
                    self.assertTrue(any(field in error for error in errors), errors)

        for value in (None, {}, "reviews/clip-01.json", [None]):
            with self.subTest(review_evidence=value):
                errors = validate_run_record(self.record(review_evidence=value))
                self.assertTrue(any("review_evidence" in error for error in errors), errors)

    def test_review_evidence_paths_are_relative_and_symlink_safe(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        try:
            root = Path(temporary.name) / "project"
            root.mkdir()
            self.assertEqual(
                validate_run_record(
                    self.record(review_evidence=["reviews/not-created-yet.json"]),
                    root=root,
                ),
                [],
            )
            invalid_paths = (
                "/tmp/review.json",
                "C:\\review.json",
                "https://example.test/review.json",
                "//[",
                "../review.json",
                "reviews/../review.json",
                "reviews/review.json?download=1",
                "reviews/review.json#page-1",
                "   ",
            )
            for path in invalid_paths:
                with self.subTest(path=path):
                    self.assertTrue(
                        validate_run_record(self.record(review_evidence=[path]), root=root),
                    )

            outside = Path(temporary.name) / "outside"
            outside.mkdir()
            link = root / "reviews"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink setup unavailable: {exc}")
            errors = validate_run_record(self.record(review_evidence=["reviews/review.json"]), root=root)
            self.assertTrue(any("escapes project root" in error for error in errors), errors)
        finally:
            temporary.cleanup()

    def test_schema_keeps_required_fields_and_exposes_optional_enums(self) -> None:
        schema = json.loads((ROOT / "schemas/generation-run.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["required"], [
            "run_id", "project_id", "clip_id", "surface", "prompt_version",
            "input_mode", "reference_tags", "prompt", "result_status", "is_synthetic_fixture",
        ])
        properties = schema["properties"]
        self.assertEqual(properties["provider_status"]["enum"], ["unknown", "queued", "processing", "completed", "failed"])
        self.assertEqual(properties["technical_qc"]["enum"], ["not_checked", "pass", "fail"])
        self.assertEqual(properties["perceptual_review"]["enum"], ["pending", "pass", "fail", "uncertain"])
        self.assertEqual(properties["review_evidence"]["type"], "array")


if __name__ == "__main__":
    unittest.main()
