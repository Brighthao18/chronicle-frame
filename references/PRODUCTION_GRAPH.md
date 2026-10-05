# One production graph — 3.2

For a new substantial production, the agent maintains `03_production_graph.json`
instead of retyping the same IDs, trims and contracts into several Markdown tables.
Research sources and human story decisions remain separate authorities. This graph
expresses the approved creative intent; compiling it does not approve any candidate.

## Compact example

The example below is schematic, not a verified historical scene. Replace the intent
with the actual approved story and register every external reference from real sources.

```json
{
  "schema_version":"3.2",
  "title":"Source-grounded threshold sequence",
  "external_refs":["SRC_GATE"],
  "frames":[
    {"id":"OPEN","route":"IMAGE25_EDIT","refs":["SRC_GATE"],"role":"opening","risk":"hero","autonomy":"REVIEW","task":"Create the approved archive-space composition around the reference gate.","keep":"Reference gate identity and geometry","change":"Surrounding light and space","composition":"Landscape, gate centred, room for a forward camera move","pixel_lock":"P1_GEOMETRY_LOCK"},
    {"id":"SEAM","route":"IMAGE25_EDIT","refs":["SRC_GATE"],"role":"SEAM","task":"Derive a closer view of the same threshold.","keep":"Same gate, lighting and axis","change":"Camera distance only","pixel_lock":"P1_GEOMETRY_LOCK"},
    {"id":"END","route":"IMAGE25_EDIT","refs":["SRC_GATE"],"role":"ending","risk":"hero","autonomy":"REVIEW","task":"Create the approved local exit state within the same setting.","keep":"Gate identity and screen direction","change":"Reveal slightly more of the surrounding space","pixel_lock":"P1_GEOMETRY_LOCK"}
  ],
  "units":[
    {"id":"U1","mode":"FRAMES","start":"OPEN","end":"SEAM","duration_s":4,"edit_s":3,"in_s":0.4,"keep":"Gate geometry and lighting","change":"Viewpoint","action":"Move gently toward the threshold and settle.","camera":"One slow forward dolly on the gate axis.","reachability":"R-A","preview_frame":"OPEN","preview_motion":"PUSH_IN"},
    {"id":"U2","mode":"FRAMES","start":"SEAM","end":"END","duration_s":4,"edit_s":3,"in_s":0.4,"keep":"Same architecture","change":"Viewpoint","action":"Reveal the surrounding space and settle.","camera":"One slow pull back on the same axis.","reachability":"R-A","preview_frame":"END","preview_motion":"PULL_OUT"}
  ],
  "joins":[
    {"id":"J1","from":"U1","to":"U2","type":"EXACT_SEAM","seam":"SEAM","exit":"Stable threshold","entry":"Same stable threshold","direction":"Same axis","handles":"0.4 s","fallback":"Revise the two local endpoints; retain the narrative"}
  ],
  "preview":{"width":640,"height":360,"fps":25}
}
```

The example uses independent source-anchored hero studies so that G2 can review opening and ending together. After G2, derive production refinements from the accepted visual masters, updating refs in the graph.

P2/P3 factual surfaces still require source overlays and their receipts; use
HYBRID_IMAGE25_CODE plus the overlay workflow when the reference contains locked
archival pixels. Example P1 geometry preservation is not proof of exact source pixels.

## Compile and execute

```text
python -X utf8 scripts/prepare_production.py "<project>"
```

This validates the graph, builds five consistent plans, compiles image and Flow queues,
synchronizes the durable runtime, then writes `06u_agent_runboard.json` with ready jobs,
review work and existing attempts to observe. Continue with the real tool execution
loop in EXECUTION_PROTOCOL.md. It never creates a fake receipt or approves a gate.

The generated plans are:

- `03d_frame_asset_plan.md` — image states and references.
- `05f_shot_endpoint_plan.md` — unit modes, references and exact usable trims.
- `04c_flow_prompt_blueprints.md` — action/camera/continuity contracts.
- `05h_join_contracts.md` — explicit adjacent joins.
- `05v_animatic_timeline.json` — frame-based preview timing.

Edit the graph, not these derived plans. An unchanged graph is a no-op. Authored
tables are never silently replaced: only pristine initializer templates or unchanged
previous compiler outputs can be adopted. If a generated table was edited, reconcile
the intended change into the graph, preserve the manual copy, and restore the last
compiled version before recompiling. Exceptions roll back touched files and retained
before-images allow recovery; a killed process may require inspection of those backups.

The validator rejects missing references, duplicate IDs, cycles, unknown fields,
invalid/NaN timing, trims beyond source duration, and missing or contradictory joins.
It does not silently invent a transition or a missing motion prompt. List external
reference IDs explicitly; registration and source verification happen before dispatch.

## Fields

Frame essentials: `id`, `route`, `task` for image generation/edit routes, and `refs` for
edits. Optional: `role`, `risk`, `autonomy`, `candidate_n`, `pixel_lock`, `keep`,
`change`, `composition`, `post`, `text_policy`, `output`, `model`, `preview_path`.
Model values remain preferences, subject to actual tool controls.

Unit essentials: `id`, `mode`, `duration_s`, `edit_s`, and for Flow `action`, `camera`.
Mode-specific fields: `start`, `end`, `ingredients`, `source_video`. Optional: `shot`,
`in_s`, `risk`, `autonomy`, `candidate_n`, `keep`, `change`, `environment`, `light`,
`focus`, `choreography`, `audio`, `reachability`, `bridge`, `story_beat`,
`preview_frame`, `preview_motion`. `source_video` may name a registered external
clip or an earlier unit; generated predecessors must be accepted first.

`mode: "CODE"` marks a unit that Claude Code (or another author) renders locally from a
scene program: it still needs `action` and `camera`, lists every asset the program may read
in `ingredients`, treats `start`/`end` as endpoint contracts and accepts no `source_video`
or incoming `FLOW_EXTEND`. The optional top-level `render` object (`width`, `height`, `fps`;
default 1920x1080 at 25 fps) fixes the format of every `CODE` unit.
[Claude Code video](providers/CLAUDE_CODE_VIDEO.md) describes the route.

Join essentials: `id`, `from`, `to`, `type`, `fallback`. Optional: `seam`, `exit`,
`entry`, `direction`, `handles`, `reset`, `audio`, `overlay`. Every pair of adjacent
units needs an explicit join. EXACT_SEAM requires the same previous end/next start ID.

Newlines and literal `|` in plan-cell text are rejected because retained table readers
cannot round-trip them. Use clear single-line instructions. No content is silently
truncated or rewritten to make the compiler pass.

## Playable animatic before G2

```text
python -X utf8 scripts/build_animatic.py "<project>"
```

Frame choice is: explicit `preview_path`, intact registered state, or the highest-ranked
passing reviewed candidate. The last may still await the human G2 decision. Every
preview unit must have a real still—missing images stop a partial preview from being
presented as a complete animatic. For T2V/Ingredients units supply `preview_frame`.

The script renders code motion, complete ordered timing and optional scratch audio
(`preview.audio`, a local file beginning at time zero). It makes a playable MP4, HTML
review page and a receipt containing source hashes and time markers, under `previews/`.
Changed inputs make a new version automatically; matching output hashes allow resume.

This is a **still-based timed preview**, not a Flow generation test. Use it to review
rhythm and visual intent; test difficult real motion in Flow afterward. It changes no
asset approvals or human gates. A frame derived from an unapproved hero cannot be used
as a production reference until that hero is accepted; for early G2 coverage use
independent concept candidates or explicit provisional preview images.
