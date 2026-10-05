# Endpoint Reachability and Motion-First Prompting

Use this reference before any expensive AI-video generation, especially when the project uses first/last frames, carried tail frames, or a model limited to **3 reference images** and **10 seconds** per clip.

## Core rule: judge reachability before writing the prompt

A start frame and an end frame are not merely two attractive pictures. They define a motion problem.

Before generation, classify the endpoint relationship:

### R-A — small / locally reachable
Same subject, same scene, same camera family, small camera or object movement, little new occlusion.

Default route:
- start-image I2V or explicit FLF if supported;
- usually 3–5 s;
- no bridge frame needed.

### R-B — medium / generatively reachable
Same identity and scene but meaningful viewpoint, pose, occlusion, scale, or camera-path change.

Default route:
- explicit first+last frame if the model truly supports it;
- otherwise strong start frame + one end-target reference;
- usually 4–7 s;
- keep only one primary action and one camera path.

### R-C — high burden, same visual world
The start and end still belong to the same scene/subject, but many invariants and changes compete: large viewpoint shift, heavy occlusion, major pose change, substantial composition change.

Default route:
- design a bridge keyframe around 40–60%;
- split into two local transitions;
- usually 2–5 s + 2–5 s;
- do not force one 10-second clip merely because the model allows 10 seconds.

### R-D — semantic / scene transition
Different era-space, different scene, topology, architecture, or conceptual state.

Default route:
- do **not** assume a single generative morph is the best solution;
- prefer occlusion-assisted transition, match cut, compositing, motion graphics, or multiple segments with a reset;
- use AI only for the local motion inside each side of the transition.

## Endpoint burden checklist

For every intended start/end pair, inspect:
- identity / subject consistency;
- camera view and focal-length family;
- framing / crop / scale;
- background geometry;
- object topology;
- occlusion / newly revealed regions;
- lighting direction / color balance;
- style / texture;
- semantic scene / era / material state;
- critical text/signage;
- implied motion cues already present in the images.

The more dimensions that change simultaneously, the less suitable the pair is for one generation.

## Clean-start rule

The start frame must behave like a real motion starting state, not a poster.

Reject or repair a start frame if it contains:
- motion blur inconsistent with the requested motion;
- warped faces/hands/architecture;
- compression artifacts;
- corrupted Chinese signage;
- dust, speed streaks, flying debris or other cues that contradict the requested motion;
- a composition that already looks like the action has finished.

## Natural-end rule

The end frame should be a state that can be reached continuously.

For continuity-sensitive shots, preserve unless the story explicitly changes them:
- identity;
- architecture/object geometry;
- lens/viewpoint family;
- primary light direction;
- background spatial logic;
- aspect ratio/crop system.

If the end frame looks like a new poster rather than a natural future state, redesign it.

## Bridge-keyframe rule

If the transition is R-C, or if R-B repeatedly fails for the same reason, design a bridge frame around 40–60% of the visual journey.

The bridge frame must:
- reduce the number of simultaneous changes;
- preserve the important invariants;
- make each half independently reachable;
- not merely be a random aesthetic midpoint.

## Occlusion is a production tool

When two states are semantically distant, move the discontinuity into a motivated occlusion or edit.

Examples:
- gate opening fills the frame → reset behind the occlusion;
- paper edge crosses the frame → reveal a different archival layer;
- dark doorway / column / photo border covers most of the frame → match to a new era-space;
- route line reaches frame edge → continue from a new map or gate edge.

This is often more controllable and more cinematic than forcing a semantic morph.

## Prompt compression rule for I2V

When the frame already defines subject, composition, color, lighting, and style, the video prompt should mostly describe **how the frame changes over time**.

Preferred order:
1. camera mode / one main camera path;
2. one primary subject or layer action;
3. environmental response only if needed;
4. temporal sequence / speed;
5. stable end condition;
6. continuity locks only when the model needs them.

Avoid:
- repeated descriptions of clothing, colors, architecture, and lighting already visible in the frame;
- generic filler such as `cinematic, epic, dynamic, beautiful` without observable instructions;
- multiple incompatible camera moves;
- multiple story beats in one shot;
- model parameters inside prose when they belong in structured fields.

## Motion budget

A useful engineering rule for short AI shots:
- one primary narrative change per second at most;
- one primary subject/layer action per shot;
- normally one major camera movement axis, at most two compatible axes;
- if the prompt needs several `then / after / finally` clauses, consider splitting the shot.

## Positive constraints vs negative prompts

Store forbidden states in a structured `FORBIDDEN / RESET` field.

Do not blindly paste a universal negative-prompt list into every model. Some platforms support explicit negativePrompt fields; others respond better to direct positive phrasing.

## Boundary snap / tail-frame rule

For first/last-frame generation, inspect the **first and last 10%** of the clip separately.

Common failure:
- motion is acceptable in the middle;
- final frames suddenly snap or “magnetize” into the supplied end frame.

When chaining:
- do not automatically export the literal final frame;
- inspect approximately the final 10–20% and select the cleanest stable frame *before* any final snap;
- save it as the carry frame only if geometry/identity are intact;
- if the clip never reaches a stable cuttable state, reset rather than passing the defect downstream.

## Candidate policy

For hero transitions:
- first pass: generate 3 candidates when cost permits;
- if all fail on the same dimension, change endpoint/path/prompt — do not just keep rerolling;
- only scan more randomness after the constraints themselves are plausible.

For simple utility shots, 1–2 candidates may be enough.

## Generation-method routing

Before a video prompt exists, choose one production method:

- `I2V_START` — start image anchors appearance; prompt defines motion.
- `FLF` — explicit first+last-frame generation when truly supported.
- `BRIDGE_2STEP` — bridge keyframe splits a hard transition.
- `OCCLUSION_2STEP` — two local clips joined under a motivated occlusion.
- `MATCH_CUT_EDIT` — deterministic editorial transition.
- `COMPOSITE_2_5D` — layered archival composite with virtual camera.
- `MOTION_GRAPHIC` — maps, lines, dates, document geometry.
- `ARCHIVAL_HOLD` — still evidence with controlled editorial treatment.
- `LIVE_OR_EXISTING_VIDEO` — use real footage when it is stronger and safer.

A professional AI-video workflow is allowed to decide **not to use AI video for a shot**.

## Required working file

Create `05d_endpoint_reachability.md` before final prompt compilation.

Suggested table:

| Shot | Start anchor | End anchor | Intended change | Identity | Camera/view | Composition/scale | Geometry/topology | Lighting/style | Scene/semantic | Occlusion | Start clean? | End natural? | Reachability | Route | Bridge frame | Target duration | AI value | Decision / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|---|

Reachability values: `R-A / R-B / R-C / R-D`.

AI value values:
- `HIGH`: generative motion creates something difficult to achieve deterministically;
- `MEDIUM`: useful, but deterministic fallback is credible;
- `LOW`: editing/compositing is more reliable than generation.
