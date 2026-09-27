# Seedance Studio

**Seedance Studio** is the local v7.2.0 single-entrypoint operating guide for source-gated Seedance 2.x production. Detailed guidance is served from the registered static HTML knowledge base.

Use `$<seedance-studio>` in Codex or `/seedance-studio` in Claude Code for Seedance 2.0 and Seedance 2.5 video work: prompt writing, prompt budgeting, connected clip planning, continuation, first/last-frame workflows, image/video/audio references, dialogue and lip-sync, professional delivery planning, API/provider guidance, multilingual prompt wording, safety rewrites, and failed-output troubleshooting.

Duration and prompt limits remain surface-specific. The skill records Seedance 2.5's verified 30-second model capability while keeping provider prompt budgets separate.

## v7.2.0 HTML knowledge migration

- `SKILL.md` is the short invocation entrypoint with the mandatory root gates.
- `references/index.html` and `references/operating-loop.html` route to the complete migrated knowledge surface.
- The 28 capabilities map one-to-one to `references/capabilities/*.html`; integrated references, six vocabularies, three native guides, and labeled historical documents are registered in `data/knowledge-map.json`.
- Existing schemas, examples, evals, golden prompts, source registry, license, invocation policy, and validation fixtures remain in their original formats. Optional generation evidence fields preserve legacy record compatibility. Source-bound production lessons cover observed generation state, reference conflicts, camera continuity, and perceptual lip-sync review; see [generation handoff](references/generation-handoff.html).

## v7.0.0 Breaking Change (historical consolidation)

- The only user-invocable skill name is `seedance-studio`.
- Former standalone Seedance sub-skills are now one-to-one documents below `references/capabilities/`.
- Former `references/` and `docs/` material is preserved as registered HTML documents.
- Legacy invocation aliases are intentionally not kept.
- Validation scripts now check the single-entrypoint layout and actual registered HTML content.

## Capability Map

| Need | Use inside the registered HTML knowledge base |
|---|---|
| Vague idea or missing brief | `references/capabilities/seedance-interview*.html` |
| Production-ready prompt | `references/capabilities/seedance-prompt.html` |
| Compact 30-100 word prompt | `references/capabilities/seedance-prompt-short.html` |
| Long story or connected clips | `references/capabilities/seedance-sequence.html` |
| Continue accepted footage | `references/capabilities/seedance-continuation.html` |
| Camera, motion, lighting, style, VFX, audio, characters | Matching files in `references/capabilities/` |
| Genre template or reusable pattern | `references/capabilities/seedance-recipes.html` |
| Blocked or unsafe prompt | `references/capabilities/seedance-filter.html` and `seedance-copyright.html` |
| Bad result | `references/capabilities/seedance-troubleshoot.html` and `references/retake-protocol.html` |
| Storyboard reference | Storyboard Reference Workflow: isolated candidates, batch approval, then rough blocking/camera flow only |
| API, provider, model IDs, workflow | `references/capabilities/seedance-pipeline.html` and registered API references |
| Japanese, Chinese, Korean, Spanish, Russian prompt wording | Native vocabulary and example sections |

## Native Language Notes

- Preserve reference tags exactly: `[Image1]`, `[Video1]`, `[Audio1]`, `@图1`, and similar tags are not translated.
- Japanese prompts should lock identity, wardrobe, composition, action endpoint, lighting, and sound instead of relying on vague mood words.
- Chinese prompts can be compact, but must still preserve mode, reference tags, action, camera, lighting, audio, and constraints.
- Korean prompts should turn mood into physical framing, light, timing, and room tone.
- Final subtitles, ad copy, legal text, and localized market copy should normally be added in post rather than burned into generated footage.

## Reference Assets

Every asset should have one primary role unless deliberately layered:

- identity
- first frame
- last frame
- product
- environment
- motion
- camera rhythm
- timing
- audio
- style
- storyboard (rough blocking and camera flow only; canonical identity and accepted continuity override it)

State what must transfer and what must not transfer.

Storyboard candidates remain outside active references until a human explicitly approves the full batch with approver, timestamp, and selected candidate IDs. They never transfer identity, costume, brand, dialogue, audio, lighting, environment detail, final style, panel numbers, or transition arrows.

## Longer Stories

Do not continue from the original plan alone. Continue from accepted generated footage or its actual final frame.

1. Define the final story outcome.
2. Divide the story into clip contracts.
3. Generate Clip 01.
4. Review the accepted clip or final frame.
5. Record the observed end state.
6. Compile only the next unresolved clip.

Accepted observed state overrides planned state. Rejected footage is not canon.

## Install

Replace `<verified-cpython-3.14>` with a CPython 3.14 executable (for example `python3.14`), and run from this `seedance-studio/` directory:

```bash
<verified-cpython-3.14> scripts/install_codex_skill.py --force
```

This is a legacy copy-only installer. It copies this package into
`$CODEX_HOME/skills/seedance-studio` when `CODEX_HOME` is set, otherwise into
`~/.codex/skills/seedance-studio`. Shared canonical skill destinations are
rejected, and the installer never performs a shared canonical deployment. A
shared canonical root is protected only when you set `AGENT_SKILLS_ROOT`.

Restart Codex after installation.

## Validation

Run from the `seedance-studio/` package root:

```bash
<verified-cpython-3.14> scripts/validate_skills.py --strict
<verified-cpython-3.14> scripts/knowledge_html.py .
<verified-cpython-3.14> scripts/behavior_contract_check.py --strict
<verified-cpython-3.14> scripts/eval_schema_check.py --strict
<verified-cpython-3.14> scripts/design_audit.py --strict
<verified-cpython-3.14> scripts/source_registry_check.py --strict
<verified-cpython-3.14> scripts/vocab_schema_check.py --strict
<verified-cpython-3.14> scripts/project_state_check.py --strict
<verified-cpython-3.14> scripts/continuity_chain_check.py --strict
<verified-cpython-3.14> scripts/sequence_eval_check.py --strict
<verified-cpython-3.14> scripts/generation_run_check.py --strict
<verified-cpython-3.14> scripts/prompt_lint.py --self-test --strict
<verified-cpython-3.14> -m unittest discover -s tests -v
<verified-cpython-3.14> -m compileall scripts tests
git diff --check
```

## Assets and Examples

Visual assets remain in `assets/` for README/gallery use. Examples, evals, schemas, scripts, tests, and data remain as validation and regression fixtures.

### Visual Gallery

- `assets/hero-dark.svg`
- `assets/hero-light.svg`
- `assets/skill-map.svg`
- `assets/hero-command-center.png`
- `assets/hero-global-filmmaker-mode.png`
- `assets/hero-cinematic.png`
- `assets/skill-os-infographic.png`
- `assets/skill-map-cinematic.png`
- `assets/infographic-skill-capabilities.png`
- `assets/infographic-cdn-delivery-map.png`
- `assets/infographic-reference-role-map.png`
- `assets/infographic-production-delivery.png`
- `assets/infographic-professional-qc-stack.png`

## License

MIT.
