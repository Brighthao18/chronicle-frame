# Google Flow Cinematic Prompting — v1.9

This reference replaces the overly terse v1.8 "motion-only" default.

## 1. The correction

For Google Flow / Veo, **concise does not mean skeletal**.

A good production prompt should not repeat every static detail already visible in a reference frame, but it still needs enough cinematic context for the model to understand:
- what the shot is *about*;
- what the viewer should notice;
- what kind of physical space the motion occurs in;
- how the camera observes the action;
- what atmosphere/light behavior should remain coherent;
- how the shot develops over time and where it settles.

The v1.8 failure mode was overcompression: prompts could become little more than `slow dolly + subtle motion + stable end state`. That is mechanically clear but often aesthetically underdetermined.

## 2. Two-layer design: director blueprint vs paste-ready prompt

Do not write the final Flow prompt directly from the screenplay.

First create a **director blueprint** containing:

1. `STORY_BEAT` — what changes for the audience.
2. `VISUAL_PREMISE` — one sentence describing the cinematic idea of the shot.
3. `ANCHOR_FACTS` — 2–4 visual facts that must remain recognizable.
4. `START_STATE` — observable starting condition.
5. `PRIMARY_ACTION` — one dominant action or transformation.
6. `ENVIRONMENT_RESPONSE` — only meaningful secondary motion.
7. `CAMERA_GRAMMAR` — shot size + position + one main movement, optionally one secondary axis.
8. `FOCUS / DEPTH` — if it materially shapes the shot.
9. `LIGHT / ATMOSPHERE` — only what matters to continuity or mood.
10. `TEMPORAL_CHOREOGRAPHY` — beginning / development / settling.
11. `END_COMPOSITION` — reachable visual endpoint or edit point.
12. `AUDIO_INTENT` — ambience/SFX/dialogue policy.
13. `CONTINUITY_LOCKS` — what must not drift.
14. `POST_ONLY` — exact text, maps, dates, logos, archival captions.

Then compile that blueprint to the selected Flow mode.

## 3. Prompt density by Flow mode

### T2V — rich cinematic prompt

Target: roughly **90–160 English words** when the shot needs a fully specified world.

Include:
- composition / shot size;
- subject + only identifying features that matter;
- one primary visible action;
- setting and meaningful environmental detail;
- camera behavior;
- temporal progression;
- light / palette / texture;
- end state;
- optional audio.

Do not exceed the model's temporal complexity budget just because the prompt is longer.

### START_FRAME / I2V — balanced cinematic prompt

Target: roughly **60–140 English words**.

The start frame already defines most appearance, but the prompt should still retain:
- a one-sentence scene/visual premise;
- the visual focal priority;
- one primary action;
- environment response;
- camera movement;
- timing;
- end behavior;
- atmosphere/light only if it must remain stable or intentionally evolve.

Do **not** delete all static context. Keep only the 2–4 anchor facts necessary for the model to interpret the movement correctly.

### FRAMES — path prompt

Target: roughly **60–140 English words**.

The main problem is not describing the first and last frame separately; it is describing a **causal, reachable path** between them.

Include:
- continuity of subject/architecture;
- what changes and in what order;
- how occlusion/parallax/focus/camera creates the transition;
- what must remain invariant;
- how movement slows into the final frame.

If the transition requires several unrelated transformations, do not write a longer prompt. Add a bridge frame or split the shot.

### EXTEND — continuation prompt

Target: roughly **35–80 English words**.

Preserve the established visual state and describe only the next beat, while retaining camera direction, motion energy, light, and spatial continuity.

## 4. Natural paragraph > label soup

Metadata can be structured, but the paste-ready Flow prompt should usually read as **one coherent cinematic paragraph**.

Bad:

```text
CAMERA: slow dolly.
ACTION: paper moves.
ENVIRONMENT: dust.
END: gate centered.
```

Better:

```text
A restrained archival-space shot viewed along the central gate axis. The camera slowly advances through layered photographic paper while the historical gate remains the stable visual anchor. A foreground paper edge passes close to the lens, creating real depth and briefly occluding the frame; faint dust and soft paper movement provide only secondary motion. The dolly remains smooth and level, with gentle parallax between the foreground archive layer and the gate behind it. The movement gradually decelerates and settles on a clean, centered threshold composition.
```

## 5. Preserve one cinematic idea per shot

A shot may contain multiple visible micro-events, but they must serve **one dominant cinematic idea**.

Examples:
- `reveal through occlusion`
- `move from evidence detail to spatial context`
- `route line carries the viewer into a new place`
- `multiple archival items accumulate into proof`
- `present threshold visually rhymes with historical threshold`

Do not combine: `reveal + era morph + orbit + crowd action + weather transformation + title reveal`.

## 6. Camera grammar

For reliability:
- one primary camera movement axis;
- optional second subtle axis only if it supports the first;
- specify speed character: restrained / even / accelerating / decelerating;
- specify the *reason* for the move in visual terms, not abstract intention;
- prefer physical camera language: dolly, track, pan, crane, locked-off, arc;
- avoid vague `dynamic cinematic camera`.

## 7. Temporal choreography

A Flow prompt should make time legible.

Use one of:

```text
At first ... Then ... By the final seconds ...
```

or

```text
0–2s ... 2–5s ... final 1s ...
```

Do not create a new scene at every timestamp. Time structure should describe phases of **one shot**.

## 8. Visual anchor facts

For I2V / Frames, retain only critical facts that influence motion interpretation.

For a historical threshold/archival sequence, examples:
- gate arch remains geometrically stable;
- central axis remains centered;
- original archival people remain frozen inside the photograph;
- paper layers exist at distinct depths;
- route line is the only graphic element that moves;
- exact Chinese signage is post-composited and is not generated.

## 9. Negative language

Do not append generic negative-prompt spam to every Flow prompt.

Prefer positive stability language in the prompt:
- `The historical photograph itself remains fixed and unchanged.`
- `The camera remains level and does not orbit.`
- `The gate geometry stays rigid throughout the move.`

Keep hard failure constraints in metadata/QC unless the active Flow model exposes a dedicated negative field that benefits from them.

See the optional [historical profile applications](../../examples/jnu-gate/references/FRAMEWORK_APPLICATION_NOTES.md) for institution-specific design.

## 11. Prompt acceptance checklist

Before pasting into Flow, ask:
- Can I visualize the shot from this paragraph without seeing the storyboard?
- Is there one dominant visual idea?
- Does the prompt preserve enough scene context to avoid a generic result?
- Does it avoid repeating the whole start image?
- Is the camera physically coherent?
- Is the time evolution clear?
- Is the final state reachable?
- Are historical text/people protected from generative drift?
- Is the prompt appropriate for the selected Flow mode?

If the answer is no, revise the blueprint before generating.

## v1.10 endpoint source-of-truth rule

Do not store independent Start/End descriptions inside the final Prompt blueprint. Use `05f_shot_endpoint_plan.md` as the single source of truth for each Flow unit's visual endpoints.

The Flow Prompt blueprint should carry cinematic context and motion language. The compiler joins it with the endpoint contract:

```text
CINEMATIC BLUEPRINT
visual premise + action + environment + camera + light + timing

+

SHOT ENDPOINT CONTRACT
Start Frame + optional End Frame + KEEP + CHANGE + PATH + reachability + carry/reset

=

PASTE-READY FLOW PROMPT
```

For `FRAMES`, the two supplied images define A and B; the prose should focus on the physically plausible path between them.
