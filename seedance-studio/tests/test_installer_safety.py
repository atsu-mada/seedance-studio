from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
INSTALLER = SCRIPTS_ROOT / "install_codex_skill.py"
PYTHON = sys.executable
sys.path.insert(0, str(SCRIPTS_ROOT))

import install_codex_skill  # noqa: E402


class InstallerSafetyTests(unittest.TestCase):
    def test_rejects_source_destination_equality_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="seedance-installer-") as raw:
            root = Path(raw)
            source = root / "source" / install_codex_skill.SKILL_NAME
            source.mkdir(parents=True)
            marker = source / "do-not-delete.txt"
            marker.write_text("keep", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "source and destination must not overlap"):
                install_codex_skill.assert_safe_destination(
                    source,
                    source.parent,
                    source_root=source,
                    canonical_root=root / "canonical",
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_rejects_source_destination_overlap_in_both_directions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="seedance-installer-") as raw:
            root = Path(raw)
            source = root / "source" / install_codex_skill.SKILL_NAME
            nested_destination = source / "nested" / install_codex_skill.SKILL_NAME
            ancestor_destination = root / "ancestor" / install_codex_skill.SKILL_NAME

            with self.assertRaisesRegex(ValueError, "source and destination must not overlap"):
                install_codex_skill.assert_safe_destination(
                    nested_destination,
                    nested_destination.parent,
                    source_root=source,
                    canonical_root=root / "canonical",
                )

            with self.assertRaisesRegex(ValueError, "source and destination must not overlap"):
                install_codex_skill.assert_safe_destination(
                    ancestor_destination,
                    ancestor_destination.parent,
                    source_root=ancestor_destination / "staged-source",
                    canonical_root=root / "canonical",
                )

    def test_custom_canonical_root_is_rejected_before_force_deletion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="seedance-installer-") as raw:
            root = Path(raw)
            canonical = root / "custom-canonical"
            destination = canonical / install_codex_skill.SKILL_NAME
            destination.mkdir(parents=True)
            marker = destination / "do-not-delete.txt"
            marker.write_text("keep", encoding="utf-8")
            environment = dict(os.environ)
            environment["AGENT_SKILLS_ROOT"] = str(canonical)

            result = subprocess.run(
                [PYTHON, "-B", str(INSTALLER), "--dest", str(canonical), "--force"],
                cwd=SKILL_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(marker.is_file(), result.stdout + result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertIn("shared canonical", result.stderr)


if __name__ == "__main__":
    unittest.main()
