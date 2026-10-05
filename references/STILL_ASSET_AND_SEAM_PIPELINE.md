# Still-Asset + Seam-First Production Pipeline

This reference defines the v2 production architecture for AI-assisted historical short films, especially when **Google Flow** is the video generator and a coding agent can call **ChatGPT Image 2.5** or another high-quality image tool for still-frame creation/editing.

The key change is simple:

> **Build the visual world as approved still states first; ask Flow to animate only the change between those states; design the boundary between adjacent shots before generation.**

This reduces identity drift, historical-text corruption, endpoint improvisation, wasted long generations, and manual editorial discovery.

## 1. Five different visual objects

Do not conflate these:

1. **Evidence plate** — verified archival pixels, document crop, signage, map, photograph, or exact source geometry that must not be rewritten.
2. **Shot endpoint frame** — the exact visual state used to start or end one Flow shot.
3. **Junction / seam frame** — a deliberately planned frame shared by two adjacent shots so they can join with little or no manual transition work.
4. **Bridge frame** — an intermediate visual state added only because A→B is not locally reachable in one generated motion.
5. **Carry frame** — a post-generation frame extracted from an approved clip. It is opportunistic, not the primary continuity design in v2.

The v1.x pipeline leaned heavily on carry frames. v2 keeps them as a fallback, but **planned seam frames come first**.

## 2. Still-asset route taxonomy

Every start/end/seam/bridge frame must have one build route in `03d_frame_asset_plan.md`.

### `SOURCE_LOCKED`
Use the original or approved restoration as-is, with only deterministic crop/scale/color normalization.

Best for:
- archival photographs;
- historical people;
- exact gate signage;
- documents;
- maps whose labels must remain exact.

### `CODE_COMPOSITE`
Assemble approved pixels using Python/Pillow, SVG, ImageMagick, HTML/CSS, or equivalent code-driven layout.

Best for:
- evidence walls;
- contact sheets;
- photo-card layouts;
- route/map graphics;
- title-safe compositions;
- exact masks, borders, typography, and geometric alignment.

### `IMAGE25_EDIT`
Use ChatGPT Image 2.5 through the agent's image-generation/editing capability to edit an existing approved image while preserving its identity/geometry contract.

Good uses:
- background cleanup;
- non-evidentiary extension of a canvas;
- removing modern clutter when clearly framed as reconstruction;
- neutral paper/background creation;
- controlled lighting harmonization;
- generating a clean visual state that does not alter sealed evidence.

### `IMAGE25_SYNTH`
Use ChatGPT Image 2.5 to create a new metaphorical/reconstruction still that is **not itself evidence**.

Good uses:
- abstract threshold space;
- neutral paper environments;
- clearly disclosed reconstruction backgrounds;
- visual metaphors whose factual content is carried by preserved archival layers.

### `HYBRID_IMAGE25_CODE`
Preferred when a frame needs both generative atmosphere and exact evidence.

Workflow:
1. generate/edit the non-critical background with ChatGPT Image 2.5;
2. composite verified archival pixels back on top with code;
3. lock text, faces, signage, borders, and map labels after generation;
4. approve the final flattened frame as the endpoint/seam asset.

This is the default for many historical threshold films composite frames.

### `POST_GRAPHIC`
No generative image step. Build the exact frame in post with code/NLE/graphics.

Best for:
- dates;
- Chinese captions;
- place names;
- route labels;
- credits;
- AI disclosure;
- exact diagrams.

## 3. What “deterministic” means in this pipeline

ChatGPT Image 2.5 is generative and therefore not pixel-deterministic. In v2, **deterministic means the final composition contract is deterministic**:

- critical source pixels are frozen;
- layout and crop are specified;
- text is not delegated to the image model;
- masks/overlays are code-controlled;
- the final approved frame is versioned and reused verbatim.

If a generated background changes between attempts, that is acceptable only if the sealed evidence and approved composition contract remain intact.

## 4. Pixel-lock classes

Each frame asset should assign one of these:

- `P0_FREE`: no historical identity or exact text; fully generative.
- `P1_GEOMETRY_LOCK`: architecture/object proportions must not drift.
- `P2_EVIDENCE_LOCK`: archival/photo/document pixels must remain unchanged.
- `P3_TEXT_IDENTITY_LOCK`: Chinese text, signage, faces, names, dates, logos, or document details are sealed and must be overlaid from source.

For `P2/P3`, never approve a frame solely because it “looks right.” Compare it to the source.

## 5. `03d_frame_asset_plan.md` schema

Recommended columns:

| Frame ID | Role | Used by | Source assets | Build route | Pixel lock | Composition contract | Image 2.5 task | Code/post task | Exact text/post-only | Approval |
|---|---|---|---|---|---|---|---|---|---|---|

Roles:
- `SHOT_START`
- `SHOT_END`
- `SEAM`
- `BRIDGE`
- `COMPOSITE_MASTER`
- `TITLE_CARD`
- `STYLE_REF`

The same approved frame may serve multiple roles.

## 6. ChatGPT Image 2.5 job contract

When the coding agent has an image tool, do not stop at writing prompts. For `IMAGE25_EDIT`, `IMAGE25_SYNTH`, and `HYBRID_IMAGE25_CODE` rows that are approved for execution, the agent should call the image tool directly and save the output under a stable frame ID.

If direct image-tool access is unavailable, compile the job into `06i_image25_job_pack.md` instead.

Every job should state:

```text
JOB ID
FRAME ID
GOAL
INPUT REFERENCES
SEALED / LOCKED PIXELS
MUTABLE AREAS
COMPOSITION
LIGHT / COLOR / MATERIAL
WHAT MAY CHANGE
WHAT MUST NOT CHANGE
NO GENERATED TEXT
OUTPUT SIZE / ASPECT
FOLLOW-UP CODE COMPOSITE
ACCEPTANCE CHECKS
```

For edit tasks, the prompt should describe the requested change, not re-describe everything visible in the input image.

## 7. Flow receives motion, not unresolved art direction

After a start/end frame is approved, Flow should receive a motion contract:

```text
KEEP
CHANGE
PATH
CAMERA
TIMING
END BEHAVIOR
AUDIO POLICY
```

For I2V / Frames-to-Video, the frame already defines most static content. The prompt should focus on:
- one main subject/layer action;
- one camera action;
- environment response;
- speed/direction;
- chronological path;
- how the motion settles into the endpoint.

Do not force Flow to generate dates, captions, Chinese signage, route labels, or precise archival layouts.

## 8. Seam-first shot chaining

Create `05h_join_contracts.md` before final generation.

Every boundary between adjacent shots gets a join type.

### `EXACT_SEAM`
Shot N ends on frame `JF_x`; Shot N+1 starts from the same exact frame `JF_x`.

Use when:
- the visual world is continuous;
- a photo/card/doorway/graphic can become a shared boundary;
- direct concatenation is desired.

Preferred endpoint design:
- Shot N converges to `JF_x` and settles briefly;
- Shot N+1 starts exactly at `JF_x` and departs from it.

### `FLOW_EXTEND`
Use Flow Extend when the next unit is literally continuation of the same movement/world.

Do not use Extend to hide a conceptual scene change.

### `MATCH_CUT`
End and start are not identical, but geometry/axis/shape/action is intentionally matched.

Examples:
- gate arch → photograph border;
- vertical pillar → map line;
- dark doorway → dark archival margin.

### `OCCLUSION_RESET`
End on a near-full occlusion or darkness; next shot starts from a new world hidden behind it.

Use for:
- cross-era changes;
- present → historical gate;
- incompatible architecture;
- major semantic resets.

### `GRAPHIC_RESET`
Use a deterministic map/document/black/title frame as a clean reset.

### `HARD_CUT`
Use when discontinuity itself is the point. It must be editorially motivated, not accidental.

## 9. Join contract schema

`05h_join_contracts.md` should contain:

| Join | From unit | To unit | Join type | Shared seam frame | Exit state | Entry state | Screen direction | Motion energy | Luma/color | Audio bridge | Handles | Auto-assembly rule | Approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

The goal is not “every cut invisible.” The goal is **every cut pre-decided**.

## 10. Direct-assembly rules

To minimize manual editing:

1. Lock final edit duration before generation.
2. Generate the shortest supported Flow duration that still provides the shot plus a small handle.
3. Prefer 4/6/8-second native Flow clips when those match the selected mode; do not generate 10 seconds by habit if the final shot is 3–5 seconds.
4. Give every shot a planned usable interval.
5. Give every adjacent pair a join contract.
6. Use a shared seam frame whenever that improves continuity.
7. Keep text and credits on deterministic tracks.
8. Treat the final assembly as execution of an already approved edit, not as discovery.

The compiler may produce:
- `06j_flow_generation_queue.md`
- `06k_direct_assembly_manifest.csv`
- `06l_direct_assembly_runbook.md`

The manifest should be sufficient to reproduce the intended cut order and trim points.

## 11. Handles

For direct-assembly work, excessive handles create work rather than safety.

Recommended default:
- 0.25–0.75 seconds of clean handle on each side when possible;
- more only for difficult transitions or uncertain motion;
- zero extra handle for exact still holds/title cards when the timing is already deterministic.

Do not assume a universal one-second handle if it forces longer or more expensive Flow generations.

## 12. Failure policy

Reject a clip when any of these fail:
- endpoint identity/geometry;
- sealed text or archival pixels;
- movement direction;
- first 10% boundary;
- last 10% boundary;
- seam compatibility with the next shot;
- cuttability at the planned usable interval.

After two failures with the same failure dimension, redesign one of:
- endpoint frame;
- seam frame;
- motion path;
- Flow mode;
- shot duration;
- bridge/reset route.

Do not keep rerolling an impossible endpoint pair.

## 13. Why this pipeline is appropriate for historical films

Historical short films often contain assets that the video model should **not reinterpret**: people, architecture, signs, documents, captions, routes, and source photographs. A still-first pipeline lets the project use generative models where they add value while keeping evidence-bearing pixels and editorial structure under explicit control.
