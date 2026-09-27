# Golden Prompt: Storyboard Reference Workflow

## Source Brief

Create a rough storyboard batch for one subject crossing the frame, pausing, and turning toward the exit. Canonical references define the approved character identity and environment. Accepted continuity state defines the opening state. The intended composition is a readable silhouette, left-to-right movement, and medium-wide framing.

## Internal Prompt Specification

Create `GridTileStyle` candidates outside active references and canonical state. Use white or pale paper, black-gray line art, sparse backgrounds, readable shape/orientation/action/placement/camera flow, and permit panel numbers and transition arrows only as planning annotations. Exclude captions, logos, watermarks, color fills, finished illustration, and strong shading.

For every candidate, record candidate ID, batch ID, inputs, prompt version, dimensions, hash, provenance status, authorization status, risk status, reviewer result, selection status, and approval status. Start as `isolated`. Review the full batch with a human. If provenance or authorization is missing, stop before approval. Hold the batch at `pending_approval` until explicit approval records approver, timestamp, and selected candidate IDs. Pending or rejected candidates cannot promote. Keep active references, canonical state, final prompts, and parent sources unchanged until approval. Regeneration uses exactly one reason: `finished-look`, `too-rough`, `unclear-action`, `unclear-layout`, or `unwanted-text`.

## Compiled Natural-Language Prompt

Use only the selected approved storyboard candidate with the canonical references and accepted continuity state. [Storyboard1] storyboard controls rough blocking and camera flow only; do not transfer start frame, final visual style, lighting, character identity, costume, or environment detail. Canonical references control identity and environment; accepted continuity state controls the opening state. Do not render source-panel numbers or transition arrows in generated video. Keep the storyboard limited to rough blocking, subject placement, and camera flow; do not introduce storyboard-derived identity, costume, brand, dialogue, audio, lighting, environment detail, or style.

## Lint Result

lint: pass

## Control-Critical Sentences

why this remains: the exact storyboard sending phrase isolates rough blocking and camera flow from start frame, final style, lighting, identity, costume, and environment detail.

why this remains: canonical identity and accepted continuity state take precedence, so storyboard planning cannot overwrite approved identity or the observed opening state.

why this remains: full-batch approval metadata and the no-promotion rule keep isolated, pending, and rejected candidates out of active project state.

why this remains: panel numbers and transition arrows are planning annotations only and never transfer into generated video.
