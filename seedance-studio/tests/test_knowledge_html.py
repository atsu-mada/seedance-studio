from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from behavior_contract_check import contract_errors  # noqa: E402
from knowledge_html import validate_registered_html, visible_text  # noqa: E402


class KnowledgeHtmlNegativeTests(unittest.TestCase):
    def copy_package(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        target = (Path(temporary.name) / "seedance-studio").resolve()
        shutil.copytree(ROOT, target)
        return temporary, target

    def test_actual_html_gate_removal_fails(self) -> None:
        temporary, target = self.copy_package()
        try:
            path = target / "references/capabilities/seedance-continuation.html"
            source = path.read_text(encoding="utf-8")
            self.assertIn("observed_end_state", source)
            path.write_text(source.replace("observed_end_state", "removed_gate", 1), encoding="utf-8")

            errors = contract_errors(target)
            self.assertTrue(any("observed_end_state" in error for error in errors), errors)
        finally:
            temporary.cleanup()

    def test_broken_registered_link_fails(self) -> None:
        temporary, target = self.copy_package()
        try:
            path = target / "references/index.html"
            source = path.read_text(encoding="utf-8")
            self.assertIn('href="operating-loop.html#operating-loop"', source)
            path.write_text(
                source.replace(
                    'href="operating-loop.html#operating-loop"',
                    'href="missing.html#operating-loop"',
                    1,
                ),
                encoding="utf-8",
            )

            errors = validate_registered_html(target)
            self.assertTrue(any("broken link" in error for error in errors), errors)
        finally:
            temporary.cleanup()

    def test_migrated_html_preserves_technical_underscores(self) -> None:
        checks = {
            "references/capabilities/seedance-sequence.html": (
                "sequence_first_clip",
                "seamless_continuation",
            ),
            "references/capabilities/seedance-interview.html": ("standalone_clip",),
            "references/capabilities/seedance-troubleshoot.html": ("observed_end_state",),
            "references/source-registry.html": (
                "https://docs.byteplus.com/en/docs/byteplus_las/video_gen_enhanced",
                "https://openaccess.thecvf.com/content/CVPR2026/papers/Hua_VABench_A_Comprehensive_Benchmark_for_Audio-Video_Generation_CVPR_2026_paper.pdf",
            ),
        }
        for relative_path, snippets in checks.items():
            text = visible_text(ROOT / relative_path)
            for snippet in snippets:
                with self.subTest(relative_path=relative_path, snippet=snippet):
                    self.assertIn(snippet, text)

    def test_duplicate_html_id_fails(self) -> None:
        temporary, target = self.copy_package()
        try:
            path = target / "references/index.html"
            source = path.read_text(encoding="utf-8")
            path.write_text(source.replace("</main>", '<p id="knowledge-index">duplicate</p></main>', 1), encoding="utf-8")

            errors = validate_registered_html(target)
            self.assertTrue(any("duplicate HTML id `knowledge-index`" in error for error in errors), errors)
        finally:
            temporary.cleanup()

    def test_all_local_resources_are_checked(self) -> None:
        temporary, target = self.copy_package()
        try:
            path = target / "references/index.html"
            source = path.read_text(encoding="utf-8")
            stylesheet = '<link rel="stylesheet" href="../assets/knowledge-base.css">'
            replacement = (
                '<link rel="stylesheet" href="../assets/missing.css">\n'
                f"{stylesheet}"
            )
            source = source.replace(stylesheet, replacement, 1)
            source = source.replace("</main>", '<img src="../assets/missing.png" alt="missing">\n</main>', 1)
            path.write_text(source, encoding="utf-8")

            errors = validate_registered_html(target)
            self.assertTrue(any("missing local link resource" in error for error in errors), errors)
            self.assertTrue(any("missing local img resource" in error for error in errors), errors)
        finally:
            temporary.cleanup()

    def test_unregistered_html_document_fails(self) -> None:
        temporary, target = self.copy_package()
        try:
            orphan = target / "references/orphan.html"
            orphan.write_text(
                '<!doctype html><html lang="en"><head><title>Orphan</title></head>'
                '<body><main id="orphan"><h1>Orphan</h1></main></body></html>',
                encoding="utf-8",
            )

            errors = validate_registered_html(target)
            self.assertTrue(any("references/orphan.html: unregistered HTML document" in error for error in errors), errors)
        finally:
            temporary.cleanup()

    def test_malformed_map_shapes_fail_without_traceback(self) -> None:
        variants = ("null", "[]", "topic-id-list", "topic-status-list")
        for variant in variants:
            temporary, target = self.copy_package()
            try:
                path = target / "data/knowledge-map.json"
                if variant in {"null", "[]"}:
                    path.write_text(variant, encoding="utf-8")
                else:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if variant == "topic-id-list":
                        data["topics"][0]["id"] = []
                    else:
                        data["topics"][0]["status"] = []
                    path.write_text(json.dumps(data), encoding="utf-8")

                errors = validate_registered_html(target)
                self.assertTrue(errors, variant)
                if variant in {"null", "[]"}:
                    self.assertTrue(any("top-level value must be an object" in error for error in errors), errors)
                elif variant == "topic-id-list":
                    self.assertTrue(any("invalid topic id" in error for error in errors), errors)
                else:
                    self.assertTrue(any("invalid status" in error for error in errors), errors)
            finally:
                temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
