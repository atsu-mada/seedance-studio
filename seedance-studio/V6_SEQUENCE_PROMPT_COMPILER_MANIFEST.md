# Seedance Studio Consolidation Manifest

This file preserves the historical manifest slot used by the validation suite. The active package is now the v7.2 local HTML single-entrypoint layout.

## Current Release

- Active package name: `seedance-studio`.
- Active package version: `7.2.0`.
- Active user-invocable skills: 1.
- Legacy compatibility aliases: none.
- Former sub-skills: migrated one-to-one into `references/capabilities/*.html` and routed by `SKILL.md`.
- Former references and native docs: preserved as registered HTML documents in `data/knowledge-map.json`.

## Retained Assets

- `assets/` remains for README/gallery visuals.
- `examples/`, `evals/`, `schemas/`, `scripts/`, `tests/`, and `data/` remain for validation and regression coverage.

## Behavior Contracts Retained

- Sequence Gate before Mode Gate.
- `standalone_clip` versus `sequence_project` classification.
- Accepted observed state overrides planned state.
- Rejected footage is excluded from canon.
- Completed beats cannot replay.
- Reserved future beats cannot leak early.
- Exact reference tags survive every prompt.
- Final Seedance prompts remain natural language unless the user explicitly asks for structured output.
- Storyboard candidates are isolated until explicit human batch approval; approved storyboards control rough blocking and camera flow only.

## Validation Commands

```bash
<verified-cpython-3.14> scripts/validate_skills.py --strict
<verified-cpython-3.14> scripts/content_audit.py --strict
<verified-cpython-3.14> scripts/eval_schema_check.py --strict
<verified-cpython-3.14> scripts/design_audit.py --strict
<verified-cpython-3.14> scripts/source_registry_check.py --strict
<verified-cpython-3.14> scripts/vocab_schema_check.py --strict
<verified-cpython-3.14> scripts/project_state_check.py --strict
<verified-cpython-3.14> scripts/continuity_chain_check.py --strict
<verified-cpython-3.14> scripts/behavior_contract_check.py --strict
<verified-cpython-3.14> scripts/sequence_eval_check.py --strict
<verified-cpython-3.14> scripts/generation_run_check.py --strict
<verified-cpython-3.14> scripts/prompt_lint.py --self-test --strict
<verified-cpython-3.14> -m unittest discover -s tests -v
<verified-cpython-3.14> -m compileall scripts tests
git diff --check
```
