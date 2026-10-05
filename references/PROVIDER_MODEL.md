# Provider capability model

Local preparation does not call any generation provider. A job becomes dispatchable only
after its inputs, actual human decisions, execution scope and current capability snapshot pass.
The runtime then issues a claim packet; an agent tool or operator performs the real operation.
A receipt must record the actual observed handle and evidence before ingestion.

Use `image` and `video` capability slots. The legacy `flow` slot remains valid for old projects.
Image snapshots record availability, observation time/evidence, execution kind and observed
model selection. Do not populate invented model names. Video snapshots add mode-specific
durations, maximum verified references and observed conditioning flags:
`first_frame`, `first_last_frames`, `reference_assets`, `extend`, `video_edit`.
Neutral video jobs require affirmative observed support for conditioning they need.
Legacy Flow mode declarations retain their old contract; an explicit false capability still blocks.

Supported execution kinds are `agent-tool`, `agent-image-tool`, `browser` and `operator`.
They describe a handoff, not a direct API integration. Capability observations expire after
24 hours in the existing dispatch policy. Unavailable or stale observations cannot prove that
a paid request may run. Output budgets require a real authorization reference and a positive
provider output limit; candidate counts are ceilings, not automatic spending targets.

The neutral graph routes are `IMAGE_SYNTH`, `IMAGE_EDIT`, `HYBRID_IMAGE_CODE` plus local
`SOURCE_LOCKED`, `CODE_COMPOSITE`, `POST_GRAPHIC`. The schema also accepts the old
`IMAGE25_*` routes. `IMG25_`, `FLOW_`, `SKIP_FLOW`, `Flow mode` and numbered artifact
filenames remain compatibility identifiers, without selecting a vendor by themselves.

Google Flow: browser/operator workflow, [operating reference](providers/FLOW_AUTOMATION.md).
OpenAI image generation: actual agent-image-tool workflow,
[operating reference](providers/IMAGE25_AUTOMATION.md). Use the installed tool's current schema.
Detailed legacy provider wording is retained only as conditional guidance; no static reference
establishes a current product capability, account entitlement, API or selector.

No live provider test is bundled or claimed as run. Future live tests must be marked `live`,
opt-in with `--live`, disclose possible paid credits and never run in ordinary CI.
