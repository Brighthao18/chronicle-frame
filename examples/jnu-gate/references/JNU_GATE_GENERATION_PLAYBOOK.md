> Optional historical example material. Source IDs and earlier creative decisions are illustrative.
> Recheck historical claims independently; this file grants no production authorization.
> No private source media, live-provider validation or current competition logistics are bundled.

# 《门外，是四海》 Generation Playbook

## v2 frame-first override

For the current project, apply `examples/jnu-gate/references/JNU_GATE_V2_PRODUCTION_BASELINE.md` and `references/STILL_ASSET_AND_SEAM_PIPELINE.md` before the older route examples below.

The production priority is now:

```text
approved 35-shot animatic/story logic
→ approved still states (source/code/ChatGPT Image 2.5 hybrid)
→ planned seam/junction frames
→ Flow-native duration + motion-only execution
→ direct assembly manifest
```

Important changes from the older model-neutral prompt pack:
- do not generate 10 seconds by habit; choose the shortest current Flow-supported duration that covers the final shot plus the required handle;
- do not rely on a universal 3-reference cap; plan references by role and verify the selected Flow mode;
- a planned seam frame is preferred over hoping the previous clip yields a usable carry frame;
- use ChatGPT Image 2.5 through Codex/Zcode for controlled still construction when useful, then re-overlay sealed archival/text pixels with code;
- Flow should animate approved visual states, not invent exact archive layouts, Chinese text, maps, or historical identity.

This is the project-specific execution layer for 《门外，是四海》. It exists because an archival school-history film has different generation needs from a generic cinematic short.

## Project reality

The film relies heavily on:
- verified old photographs;
- restored gates/architecture;
- historical Chinese signage;
- maps/plans/routes;
- group photographs where people must not be counterfeited into live action;
- a recurring “gate / threshold” motif.

Therefore, **AI video is not the default for every shot**. Use generation where it adds controlled spatial/temporal motion; use deterministic editing where evidence integrity and typography/geometry matter more.

## Default shot-family routing

### 1. Present-day gate observation
Preferred:
- real present-day video if available;
- otherwise restrained I2V from an approved present-gate frame.

Use AI for:
- subtle camera push / parallax / environment motion.

Do not use AI for:
- rewriting gate signage;
- changing architecture.

### 2. Present gate → historical gate
Do **not** default to a direct semantic morph between two very different gates/eras.

Preferred route: `OCCLUSION_2STEP`.

Phase A:
- start from present gate;
- camera moves toward the gate opening / column / dark threshold;
- end when a clean occluder covers most of the frame.

Reset:
- begin Phase B from an approved historical gate frame aligned to the same central axis / border geometry.

Phase B:
- continue a compatible camera move away from / through the historical threshold.

This hides the era discontinuity inside a motivated visual obstruction and gives the model two locally reachable problems.

### 3. A089 / A090 / A091 / A092 early archive cluster
Preferred route: `COMPOSITE_2_5D` or `MATCH_CUT_EDIT`.

Reason:
- these are evidence assets, not actors;
- the filmmaking value is in spatial discovery and relationship, not hallucinated human motion.

Workflow:
- compose a single approved archive-space keyframe from selected source pixels;
- preserve people/documents as still evidence;
- move camera, paper layers, focus, masks, and graphic connectors;
- only use AI video if a subtle non-human layer motion is needed.

### 4. Shanghai plan / institutional expansion
Preferred route:
- `MOTION_GRAPHIC` for plan lines, labels, route geometry;
- `COMPOSITE_2_5D` for paper / plan depth;
- optional short I2V only for controlled camera movement over a prebuilt composite.

Do not ask a video model to invent plan typography or precise cartography.

### 5. Shanghai → Jianyang rupture / route
Preferred route:
- `MOTION_GRAPHIC` + `OCCLUSION_2STEP` / `MATCH_CUT_EDIT`.

Possible visual path:
- verified plan line breaks or exits frame;
- route line continues deterministically in post;
- route reaches a frame edge / photo border / gate pillar;
- reset into Jianyang gate or archival layer.

The route motion should be editorially deterministic, not a generative hallucination.

### 6. Jianyang evidence: A176 / A177 / A184
Preferred route: `COMPOSITE_2_5D`.

Build an evidence wall / contact-sheet space:
- A176 appears and remains;
- A177 joins it;
- A184 joins it;
- the visual argument is accumulation over time.

Do not use three independent AI videos of the photos.

AI value here is normally `LOW` unless the shot uses a generated camera path over an already-approved composite.

### 7. Guangzhou rebuilding / reopening
Split the problem:
- human/event photos remain documentary layers;
- gate / building / environment may receive restrained AI camera or environmental motion if a clean reconstruction exists;
- event text and signage stay deterministic.

### 8. Final convergence
Do not ask one model to morph every historical gate into the current gate in a single 8–10 second clip.

Preferred options:
- matched geometry cuts between verified/restored gates;
- short local gate-to-gate transitions separated by occlusion;
- composite depth stack that collapses editorially into the present gate;
- final present-gate shot with subtle real/I2V movement.

## Project-specific endpoint rules

### Gate-to-gate endpoint compatibility
Normally classify direct present-gate → different historical-gate pairs as `R-D` unless the two frames were deliberately precomposed to share:
- central axis;
- similar opening scale;
- similar crop;
- stable architecture geometry;
- an occlusion/matte boundary that hides the discontinuity.

Do not “solve” an R-D pair with a longer prompt.

### Historical people
If the source is a group photo:
- Subject motion = `NONE` by default;
- face/limb animation is a fatal historical-integrity risk unless explicitly framed as stylized reconstruction and approved;
- use layer/camera/focus/graphic motion instead.

### Chinese signage
Verified text such as `暨南学校` / `国立暨南大学` should be treated as locked pixels or post-composited text.

Do not rely on video generation to redraw it.

## Three-reference allocation for this project

When chaining:
- `REF1`: approved carry frame from previous local clip;
- `REF2`: authoritative gate / archive / geometry reference;
- `REF3`: bridge or end-target composite.

For documentary composites:
- use one precomposed visual anchor as a single reference instead of spending all three slots on individual photos.

## Prompt style for this project

### Archival/composite I2V
Keep it very short.

Example:

```text
The camera advances slowly through the layered archival composition on a single central axis. The historical people and all printed text remain completely still. Only the foreground paper edge creates gentle parallax as it passes across frame. Motion stays uniform and restrained, then settles into a stable frame for the next cut. Continuous single shot.
```

Do not add long descriptions of the people, paper color, clothing, architecture, or “cinematic history atmosphere” if those are already visible in the approved frame.

### Gate local motion

```text
A slow controlled forward dolly along the gate's central axis. Architecture remains rigid and unchanged. Background depth produces subtle natural parallax. No additional camera move. The motion decelerates in the final second and settles into a clean, stable threshold composition for the next shot.
```

### Occlusion transition phase A

```text
The camera moves forward on a single axis until the dark gate opening / foreground pillar progressively fills the frame. The architecture remains rigid. No scene transformation occurs before the occlusion. End on a clean near-full-frame obstruction suitable for a hidden reset.
```

### Phase B after reset

```text
Begin from the approved historical gate frame. Continue the same perceived forward direction at a restrained speed. The gate remains rigid and all signage stays unchanged. Reveal the historical space gradually through natural parallax, then settle into the target archival composition.
```

## Candidate strategy for hero transitions

For the few hero transitions that genuinely use AI:
- generate 3 candidates first;
- inspect endpoint adherence, first/last 10%, camera obedience, geometry, and cuttability;
- if all 3 fail on the same dimension, redesign the endpoint/bridge/route;
- do not simply generate 10 more versions with the same impossible constraints.

## Project-specific failure diagnosis

| Symptom | Likely cause | First fix |
|---|---|---|
| gate melts / bends | too much semantic change or conflicting refs | reset / bridge / deterministic match cut |
| final frame suddenly snaps | end anchor too far or overly rigid | choose pre-snap carry frame; redesign endpoint |
| historical faces move | prompt/model interprets source as live scene | set subject motion NONE; use composite/2.5D |
| Chinese signage changes | generative redraw | preserve pixels / overlay in post |
| camera becomes dramatic | too many camera verbs / adjectives | one camera axis only |
| image barely moves | prompt repeats static visual facts | delete visual description; motion-only prompt |
| sequence feels like slideshow | assets treated independently | precompose relationship frame / evidence wall / motivated path |
