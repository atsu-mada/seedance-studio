---
name: seedance-studio
description: "This skill should be used when creating, improving, or troubleshooting Seedance 2.x video on any surface - Dreamina, Jimeng, CapCut, Doubao, Volcengine/Ark, BytePlus, Higgsfield, Magnific, Leonardo.AI, Runway Seedance routes, fal, or third-party provider/router surfaces - including text/image/video/reference-to-video prompts, first/last frame, dialogue, lip-sync and audio, IP-safe rewrites, API, pricing and model-ID questions, and zh/ja/ko/es/ru prompt work. Not for non-Seedance models or image-only prompting."
license: MIT
metadata:
  version: "7.3.0"
  user-invocable: true
  tags: [seedance, video, workflow]
  breaking_change: "Moved the consolidated knowledge surface to registered static HTML documents; the skill remains one single entrypoint."
---

# Seedance Studio

Seedance Studio is one user-invocable entrypoint for source-gated Seedance 2.x video work. This single-entrypoint contract routes to the detailed operating loop, 28 capability documents, integrated references, six vocabulary documents, three native-language guides, and historical release notes in the registered static HTML knowledge surface. The entrypoint retains the mandatory gates needed to choose, draft, review, and hand off a prompt safely.

## Root Operating Loop

Follow the operating loop in [`references/operating-loop.html`](references/operating-loop.html), using [`references/index.html`](references/index.html) to locate the detailed capability or reference document. The HTML documents are the content authority; the index is only a route and must not be treated as a keyword-only substitute for the linked document.

### Mandatory gates

1. **Intake gate:** identify the user's goal, production phase, target surface, mode, duration, aspect ratio, references, audio needs, deliverables, and safety or IP risks. If intake exposes a safety, IP, likeness, or evasion concern, route to the safety gate before planning.
2. **Source gate:** before platform, model, API, pricing, or availability claims, load the `api-status` and `source-registry` reference documents. For Runway, Volcengine, fal, Magnific, provider/router, or China-facing details, also load the platform-surface matrix. When a creative suite is driven by an operator skill (for example `magnific-operator`), this skill writes the suite-neutral prompt and hands execution to that skill through the generation handoff.
3. **Professional gate:** for film, advertising, campaign, client delivery, localization, color, sound, subtitles, post, QC, or multi-shot work, load professional-filmmaking standards before drafting.
4. **Sequence gate:** classify the request as `standalone_clip` or `sequence_project` before choosing a mode. Connected clips, continuation, extension, long stories, campaigns, dense action or dialogue, and ideas that exceed one reliable generation are sequence work. Sequence work must load sequence, project-state, continuation-handoff, prompt-compiler, and continuity-QC guidance.
5. **Mode gate:** choose T2V, I2V, V2V, R2V, FLF2V, edit, verified native extend, or troubleshoot before writing prose. Surface-specific availability must be checked against the current source record.
6. **Capability gate:** load the capability map and allocation model before planning a shot, mode, or budget. Route to the relevant capability HTML document rather than reproducing its content in this entrypoint.
7. **Reference gate:** assign every asset one primary role - identity, first frame, last frame, product, environment, motion, camera, timing, audio, or style - and state what must not transfer. Storyboard references require isolated candidates and explicit batch approval before promotion.
8. **Language gate:** for Chinese, Russian, Japanese, Korean, Spanish, or mixed-language prompts, load multilingual community examples and the matching vocabulary document. Preserve `[Image1]`, `[Image2]`, `[Video1]`, and `[Audio1]` exactly.
9. **Safety gate:** route IP, likeness, voice, brand, real-person, graphic, or evasion-like wording through the copyright or filter capability. Do not infer authorization from an uploaded asset.
10. **Direction gate:** before drafting a scene, load the directing engine, identify the scene function and one intention, and derive one coherent camera, lens, light, blocking, performance, and sound setup.
11. **Prompt gate:** route to interview, prompt, short-prompt, sequence, continuation, or the relevant domain capability. Final prompts remain natural language unless structured output is explicitly requested.
12. **Quality gate:** run the anti-slop and directing-coherence checks. Confirm one visible beat, one primary camera move, physically motivated light, sound intent, continuity anchors, constraints, delivery caveats, and source-date caveats.
13. **Repair gate:** when a take returns, use the retake protocol to choose keep, fix in post, edit, re-roll, rewrite, or a frame-matched partial regenerate of a flawed head or tail. Change one variable per retake and diagnose the cause before adding adjectives.

### Sequence invariants

For sequence work, do not write Clip 01 until the story objective, final outcome, ordered beats, active surface or conservative profile, clip budget, current clip job, and current completed endpoint are known. Do not write a continuation until the accepted previous clip or actual final frame has been reviewed and its observed end state recorded.

- Every sequence prompt has `project_id` and `clip_id` lineage.
- Accepted observed state overrides planned state; rejected footage never becomes canon or a continuation source.
- Future prompts remain provisional until the preceding take is reviewed.
- Exact reference tags survive every clip unchanged.
- Completed beats cannot replay, and reserved future beats cannot leak early.
- Continuity state is updated after each accepted take.

### Required continuation input

Require `project_id`, current `clip_id`, valid `parent_clip_id`, the full-story objective and final outcome, the next narrative job, an accepted previous clip or final frame, `observed_end_state`, continuity locks, the directorial voice, the exact reference registry, and an active or conservative surface profile. If the source ending is unavailable, request it instead of inventing the continuation state.

## Knowledge surface

The package is a local, static HTML knowledge base with UTF-8 `lang`, `title`, `main`, stable IDs, relative links, and local CSS. It has no build step, required JavaScript, external CDN, CMS, or generated runtime dependency.

- [`references/index.html`](references/index.html) is the registered route for every active capability, reference, vocabulary, guide, and historical document.
- [`references/operating-loop.html`](references/operating-loop.html) contains the complete migrated root loop and load map.
- `references/capabilities/` contains the 28 capabilities one-to-one, including six vocabulary capabilities and the three native examples capabilities.
- `references/` contains the integrated reference documents; `references/vocab/` contains `en`, `ja`, `zh`, `ko`, `es`, and `ru`.
- `references/guides/` contains the Japanese, Korean, and Chinese native-language guides plus clearly labeled historical design and release-readiness documents.
- `data/knowledge-map.json` is the small registered index with `schema_version`, `skill_name`, and topic entries. Validators read the actual registered HTML and verify its links, anchors, sections, and tables; an index keyword cannot make missing content pass.

Use the exact existing schemas, examples, evals, golden prompts, source registry, license, invocation metadata, and policy files shipped beside this entrypoint. The HTML migration preserves existing contracts. Optional generation-run evidence fields and source-bound production lessons extend those contracts without making old records claim new verification.

## Version and claim boundary

`7.3.0` is a local knowledge update on top of the 7.2.0 HTML reorganization: it adds field-observed suite-surface notes, suite-operator routing, and generalized production techniques. It does not claim to be an upstream Seedance release or the latest provider version. Volatile model, surface, pricing, API, and policy statements remain source-gated and date-labeled in the registered references.

## Validation contract

Run the package validators with the selected CPython 3.14 environment. The static knowledge validator must pass the registered map, UTF-8 documents, stable `main` IDs, local stylesheet, relative links and fragments, absence of executable or external resources, and one-to-one capability coverage. Existing schema, eval, source, vocabulary, sequence, behavior, generation-run, prompt-lint, installer-copy, and unit checks remain required.

## Generation evidence and review

For a submitted or interrupted job, read [generation handoff](references/generation-handoff.html). For location drift, read [street continuity](references/cases/street-continuity.html). For a speaking character, read [lip-sync review](references/cases/lipsync-review.html). Input audio integrity, technical output QC, perceptual review, and acceptance are separate evidence states.
