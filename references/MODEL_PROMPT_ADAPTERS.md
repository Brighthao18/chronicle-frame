# Model Prompt Adapters and Production Handoff

Model capabilities change quickly. Treat this file as a routing grammar, not a frozen feature matrix. If the user asks for a specific platform, verify current model names, duration limits, reference inputs, audio support, and API fields when web access is available.

## 1. Master prompt first, adapter second

Never author six unrelated prompts for six models.

For each shot, first create a **model-neutral master brief**:

1. Story purpose
2. Verified constraints / evidence IDs
3. Reference asset IDs
4. Start frame / end state
5. One primary action
6. Camera instruction
7. Environmental motion
8. Duration / pacing
9. Continuity anchors
10. Forbidden changes

Then adapt syntax and emphasis to the selected generator.

## 2. Adapter families

### Cinematic I2V/T2V adapter
Prioritize:
- subject + primary action
- camera movement
- start-frame fidelity
- spatial continuity
- physical motion
- duration
- negative constraints

### Multi-reference / reference-to-video adapter
Prioritize:
- reference role mapping (`CHAR`, `ARCH`, `ENV`, `STYLE`)
- explicit priority if references conflict
- describe only the shot-specific change after identity locks

Example role map:
- `ARCH001` controls gate geometry and signage placement
- `ENV003` controls street depth and vegetation
- `STYLE002` controls grade/texture only

### Multi-shot native adapter
Use only when a native multi-shot mode is intentional.
Specify each internal shot separately:
- duration
- shot size
- camera view
- action
- transition

Still create editorial shot IDs so the sequence can be rebuilt from separate clips if the native multi-shot result is unusable.

### Local ControlNet / pose / depth adapter
Include:
- checkpoint/model
- LoRA(s)
- ControlNet/control type
- preprocessor
- weight/strength
- reference image(s)
- sampler/scheduler if relevant
- seed
- frame count/FPS
- resolution

Do not pretend exact ComfyUI node settings are universal; record the actual workflow JSON when one is used.

## 3. Historical signage and text

Do not rely on the video model to reproduce critical historical Chinese text.

Preferred hierarchy:
1. preserve original pixels when possible;
2. use the generated frame only for geometry/environment;
3. composite verified signage/labels in post;
4. if the model must see signage for shape, quote the exact Chinese string and freeze it as an invariant, then still verify frame-by-frame.

## 4. English production prompt template

```text
SHOT {SHOT_ID} — {DURATION}s

STORY PURPOSE
{What this shot must make the audience understand or feel.}

REFERENCE MAP
{ARCH001 = geometry; ENV002 = location; STYLE001 = finish; ...}

START STATE
{Observable start frame.}

PRIMARY ACTION
{One dominant action only.}

CAMERA
{Shot size, lens feel, height, angle, movement, speed.}

ENVIRONMENTAL MOTION
{Only secondary motion that supports the shot.}

END STATE
{Observable end frame / transition target.}

CONTINUITY LOCKS
{Identity, geometry, costume, light direction, screen direction.}

HISTORICAL CONSTRAINTS
{Evidence-backed facts only.}

NEGATIVE CONSTRAINTS
{No extra people, no modern objects, no geometry mutation, no text mutation, etc.}
```

## 5. Safer fallback template

```text
FALLBACK FOR {SHOT_ID}
Preserve the same story function but simplify generation risk.
- Keep: {story information / transition / emotion}
- Remove: {complex action / crowd / long performance / unstable transformation}
- Replace with: {simpler controllable visual solution}
```

## 6. Multi-model evaluation card

When testing more than one generator, score each output 1–5 on:
- reference fidelity
- historical/asset continuity
- motion fidelity
- camera obedience
- artifact severity
- editability
- first/last-frame usefulness
- attempts needed
- approximate cost/time

Choose the most **editable and repeatable** result, not automatically the most spectacular one.

## 7. I2V motion-only adapter

When a verified/approved start frame already fixes appearance, geometry, composition, and lighting, do **not** restate them at length in the motion prompt. Use the reference map + continuity locks for identity and concentrate the model text on motion.

```text
SHOT {SHOT_ID} — IMAGE/REFERENCE TO VIDEO

STORY PURPOSE
{One sentence.}

SUBJECT MOTION
{One primary subject action. For archival people: None; preserve exact pose.}

ENVIRONMENTAL MOTION
{Only justified secondary movement/layer motion.}

CAMERA MOTION
{One controlled trajectory + speed.}

TIMING
{State progression by seconds or phases.}

END STATE
{Exact composition/state required for the next edit.}

CONTINUITY LOCKS
{ARCH/DOC/CHAR/STYLE IDs.}

DO NOT
{No geometry mutation, no extra people, no signage changes, etc.}
```

If a precise final composition matters, create/approve the end keyframe before generation and use first/end-frame capable workflows when available.

## v1.5 adapter note: 3-reference / 10-second workflows

For platforms with strict reference and duration caps, adapters must not simply truncate a richer master prompt. They should:
- preserve the shot's single primary action;
- declare which 3 references get priority and why;
- identify whether the shot starts from a carried frame or a reset anchor;
- compress motion design so it completes within the real clip limit.


## v1.7 reachability-first adapter rules

The model adapter receives a structured shot state, not a prose screenplay. It must preserve:
- production route;
- start/end/bridge references;
- 3-reference slot allocation;
- one primary motion path;
- duration as a structured parameter;
- continuity/reset conditions.

### I2V adapter
Prefer concise motion-only wording. Static appearance, lighting, palette, and architecture already defined by the image/reference should usually be omitted.

### FLF adapter
Use only if the active model genuinely supports explicit first+last-frame conditions. Describe the causal path between endpoints and a smooth natural arrival; do not just restate the two frames.

### R-C / R-D
Do not compile an oversized single prompt. Use bridge/occlusion phases or deterministic edit recipes.

### Negative constraints
Keep them structured until the target model is known. Only platforms with an appropriate negative-prompt field should receive them as a dedicated negative prompt. For direct-positive I2V models, phrase the desired stable behavior positively instead.

## v1.8 Google Flow adapter

When the active generator is Google Flow, do not treat Flow as a generic text box. First select the Flow production mode, then compile the prompt.

### Flow START_FRAME / image-to-video

The frame already fixes subject/architecture/composition/light/style. Keep the prompt motion-first:

```text
{camera starting behavior}. {one primary visible action}. {necessary environmental response}. {timing / pace}. The camera {one controlled trajectory}. The motion remains continuous and settles into {observable end behavior}. {optional ambience/SFX}.
```

### Flow FRAMES / first+last

Only after endpoint reachability has passed:

```text
Continuous single shot beginning from the supplied first frame and naturally arriving at the supplied final frame. {causal movement path}. {environment response}. The camera {trajectory} with even speed and coherent parallax. The transition develops progressively rather than morphing abruptly and settles naturally into the final composition.
```

If this requires several simultaneous changes, route to bridge/occlusion/match-cut instead of extending the prompt.

### Flow INGREDIENTS / CHARACTERS

Use Ingredients as stable identity/appearance anchors. Prompt only the shot-specific behavior/change. Do not repeatedly re-describe the entire person/gate/style bible.

### Flow EXTEND

```text
Continue the existing shot seamlessly. Preserve current screen direction, subject state, lighting, spatial continuity and camera behavior. {one next action}. {environment response}. The motion remains consistent with the previous clip and settles on {next edit point}.
```

Use Extend for continuation, not a conceptual reset or era change.

### Flow OMNI_EDIT

State the **one localized change** and what must stay unchanged. Do not use iterative editing to rescue a fundamentally unreachable motion path.

### Flow audio

For historical/documentary work, final narration should normally remain a separate post-production track. Flow-native audio may be requested for ambience/SFX or deliberately tested dialogue. Exact names, quotations and historical wording should not force regeneration of an otherwise good visual shot.

### Flow prompt language

Use concise audited English for production prompts unless the active current model/UI clearly benefits from another language. Keep exact Chinese dialogue, signage or screen-copy strings in their dedicated fields; critical historical text remains post/composite by default.
