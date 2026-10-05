# Google Flow Shot Endpoint + Seam System — v2

This reference separates **four** visual-control concepts that must never be conflated:

1. **FILM OPENING / ENDING** — the first and final visual propositions of the whole film. Story/directing level.
2. **SHOT START / END TARGET** — the endpoints of one generated Flow unit. Model-conditioning level.
3. **PLANNED SEAM / JUNCTION FRAME** — a frame deliberately shared by adjacent shots so the cut can be executed with little or no editorial invention. Assembly level.
4. **CARRY FRAME** — a clean frame extracted after a generated shot is approved. Fallback/opportunistic continuity level.

v2 is **seam-first**: when a clean join matters, design the seam before generation instead of hoping a useful carry frame appears later.

## 1. Whole-film opening and ending

Use `05a_film_opening_ending.md` only for:
- opening visual proposition;
- opening question/tension;
- ending visual payoff;
- motif transformation;
- opening/ending rhyme.

Do not use this file as the source of per-shot Flow endpoints.

## 2. Shot endpoint plan

Use `05f_shot_endpoint_plan.md` for every Flow generation unit.

Recommended schema:

| Unit | Parent shot | Flow mode | Duration | Start frame source | Start frame ID | Start role | End frame needed? | End frame source | End frame ID | End target state | KEEP fixed | CHANGE | Motion path | Endpoint distance | Reachability | Bridge/reset | Join-in seam | Join-out seam | Carry-in | Carry-out | Extraction rule | Approval |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Older v1.10 projects without `Join-in seam` / `Join-out seam` remain valid; v2 adds them during upgrade.

### Start frame

The Start Frame is the exact state from which motion begins.

A good start frame:
- is sharp and geometrically clean;
- has no contradictory motion blur;
- already reflects the intended composition family;
- contains only elements the model should inherit;
- has sealed historical pixels restored/overlaid before generation when needed.

### End frame

The End Frame is a naturally reachable future state.

Use one when it materially improves:
- a planned seam;
- a match transition;
- reveal completion;
- final camera position;
- a shared composition with the next shot.

Do not force an End Frame when a textual end state is sufficient.

## 3. Planned seam / junction frame

A seam frame is created **before generation** and is referenced by both sides of a boundary.

Example:

```text
SH012 end frame = JF_012_013
SH013 start frame = JF_012_013
```

This makes the visual boundary an explicit production asset rather than an editing guess.

A seam frame may be:
- source-locked archival pixels;
- code composite;
- ChatGPT Image 2.5 edited/synthesized still with source pixels re-overlaid;
- black/occlusion state;
- map/document state;
- approved gate/threshold frame.

The authoritative join logic lives in `05h_join_contracts.md`.

## 4. Flow-mode endpoint rules

### `T2V`
- Start frame: optional.
- End frame: usually none.
- Use mainly when continuity/geometry is low-risk.

### `START_FRAME`
- Start frame: required.
- End frame: optional.
- Preferred for a strong approved entry state with a text-described local end state.

### `FRAMES`
- Start frame: required.
- End frame: required.
- Prompt describes the **path A→B**, not both images.
- Strong fit for exact seam-to-seam movement when endpoints are locally reachable.

### `INGREDIENTS`
- Endpoints optional.
- Ingredients carry recurring identity/appearance; endpoint/seam frames still win when composition must be exact.

### `EXTEND`
- Inherits the approved existing clip state.
- Use only for true same-world continuation.
- Do not use Extend to conceal a scene/era reset.

### `OMNI_EDIT`
- Preserve the usable clip and change only the localized problem.

### `SKIP_FLOW`
- Deterministic/post route. No Flow endpoint pair required.

## 5. Reachability first

Compare start/end across:
- identity/architecture;
- camera position/direction;
- framing/scale;
- geometry/topology;
- occlusion;
- lighting/time-of-day;
- semantic/era state.

Classes:
- `R-A`: small/local change;
- `R-B`: moderate same-world change;
- `R-C`: high-burden same-world change;
- `R-D`: semantic/scene/era change.

Default routing:
- `R-A`: direct `FRAMES` / `START_FRAME`;
- `R-B`: direct only with one clear path;
- `R-C`: bridge frame or two-step generation;
- `R-D`: `OCCLUSION_RESET`, `MATCH_CUT`, `GRAPHIC_RESET`, deterministic composite, or separate shots.

Do not fix an impossible A→B pair by adding adjectives.

## 6. KEEP / CHANGE / PATH

Every endpoint-conditioned Flow shot must be reducible to:

```text
KEEP:
what must not drift

CHANGE:
what must differ by the end

PATH:
how the shot physically gets from A to B
```

Optional additions:

```text
CAMERA
TIMING
END BEHAVIOR
AUDIO POLICY
```

## 7. Endpoint timing and settling

When the End Frame is also the next shot's seam:
- approach it progressively;
- avoid a last-frame “snap”;
- settle before the usable interval ends when possible;
- reserve only the handle actually needed.

Inspect the first and last 10% frame-by-frame.

## 8. Carry frame becomes fallback, not default plan

After a clip passes:
1. inspect its final 10–20%;
2. if a better continuity frame exists than the planned seam, it may be saved as `CF_*`;
3. use it only when this improves the next shot without propagating error.

The Carry Frame:
- need not be the literal last frame;
- need not equal the planned End Frame;
- never overrides a deliberately approved seam without review;
- must not propagate text/identity/geometry defects.

## 9. Bridge rule

If A→B requires too many simultaneous changes, introduce a state around 40–60% and split it.

Example:

```text
present gate
→ near-full dark threshold / paper occlusion
→ reset
→ historical gate
```

Do not ask one clip to morph present architecture directly into historical architecture unless the transformation itself is intentionally metaphorical and has been approved as such.

See the optional [historical profile applications](../../examples/jnu-gate/references/FRAMEWORK_APPLICATION_NOTES.md) for institution-specific design.

## 11. Authority order

For Flow prompt compilation:

1. approved evidence/source pixels;
2. `03d_frame_asset_plan.md` approved still state;
3. `05h_join_contracts.md` planned seam;
4. `05f_shot_endpoint_plan.md` shot endpoints/motion contract;
5. `04c_flow_prompt_blueprints.md` cinematic wording.

If prose conflicts with an approved visual contract, the approved visual contract wins.
