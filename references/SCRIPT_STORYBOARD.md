# Script, Storyboard, and AI Prompt System

## 1. Beat outline

Before polished narration, define:

| Beat | Time | Story job | New information | Emotion | Visual carrier | Evidence IDs |
|---|---|---|---|---|---|---|

If a beat has no visual carrier, solve that before polishing prose.

## 2. AV script

Use this production format:

| Time | Audio | Visual | Evidence IDs | Production note |
|---|---|---|---|---|

Audio tags:
- `[VO]`
- `[DIALOGUE]`
- `[ARCHIVE AUDIO]`
- `[SFX]`
- `[MUSIC]`
- `[SILENCE]`

Visual source tags:
- `[ARCHIVE]`
- `[LIVE]`
- `[REENACTMENT]`
- `[AI-RECON]`
- `[MOTION-GRAPHIC]`
- `[TEXT]`

## 3. Narration craft

Prefer:
- concrete subjects
- verbs with action
- precise sensory detail when evidenced
- short sentences at major visual turns

Reduce:
- “薪火相传、弦歌不辍、砥砺前行、再谱华章” strings
- achievement catalogs
- narration that duplicates captions
- omniscient claims about what historical figures “must have felt”

A useful test:
> If the institution name were removed, would this line still describe many universities? If yes, rewrite it more specifically.

## 4. Sequence-first storyboard schema

Before shots, load `CINEMATIC_VISUAL_SYNTHESIS.md` and create sequence cards. Do not walk through source files one-by-one.

| Sequence | Time | Story turn | Asset set | Primary visual engine | Secondary device | Camera/path | Sound engine | Entry | Exit/payoff | Evidence risk |
|---|---|---|---|---|---|---|---|---|---|---|

Then break each sequence into **production shots**, not concept-image captions:

| Shot | Time | Purpose / director intent | Era/location | Size | Lens feel | Camera position/height | Angle | Movement | ONE primary action | Emotion | Composition/depth | Light/color | Source | Reference IDs | Visual engine | Assets in frame | Layer interaction | Motion source | Audio | Transition | Why this cut | Continuity | Evidence | Gen risk | Safer fallback | Prompt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

### Shot size vocabulary
- ECU / extreme close-up
- CU
- MCU
- MS
- MLS
- WS
- EWS

### Angle
- eye-level
- high angle
- low angle
- top-down
- over-shoulder
- profile
- axial/frontal

### Movement
- locked-off
- pan/tilt
- push-in/pull-out
- track/dolly
- crane
- handheld
- parallax from layered stills
- digital 2.5D only when justified

### Shot action discipline

Every AI-generated narrative shot should have **one principal action**. A shot may include subtle secondary environmental motion, but do not bundle multiple editorial beats into one generation simply because the model supports a long duration.

Typical starting durations:
- 0.5–1.5 s: hook, insert, impact detail
- 2–4 s: ordinary action/reaction
- 3–6 s: dialogue, explanation, emotional build
- 5–8+ s: establishing, atmosphere, deliberate archival hold

For controllable AI editing, prefer replaceable ~3–6 s units unless a longer shot has a clear reason.

## 5. Historical-photo motion

Do not animate every old photo with the same slow zoom. A moving crop is not automatically a moving-image idea. Prefer relationships among assets, masks, geometry, depth, graphics, and sound before synthetic person motion.

Choose based on image meaning:
- locked hold for gravity
- crop reveal for discovery
- parallax only when layer geometry is clear
- match cut to present-day geometry
- document macro scan for evidence
- restrained atmospheric movement for AI reconstruction

Avoid aggressive face/body motion from a single archival portrait unless the creative strategy explicitly accepts synthetic reenactment.

Hard guardrail: if three consecutive shots can be summarized as “single still + slow camera drift,” stop and redesign the whole sequence, not just the third shot.

## 6. Continuity / Asset Bible for AI shots

Before generating multiple connected shots, freeze reusable assets with stable IDs (`CHAR`, `COSTUME`, `PROP`, `ARCH`, `ENV`, `DOC`, `STYLE`, `AUDIO`, `REF`) and approved references. Once approved, prompts should point to the asset ID and describe only the shot-specific change.

Freeze:

### Character
- age range
- facial/hair anchors
- clothing silhouette/materials
- accessories
- posture

### Architecture/object
- proportions
- materials
- signage
- wear state
- invariant geometry

### Scene
- season/weather
- time of day
- light direction
- spatial layout
- screen direction

### Camera
- aspect ratio
- focal-length family
- camera height
- motion style
- depth-of-field logic

### Look
- palette
- contrast
- grain/texture
- archival vs reconstructed treatment

### Forbidden mutations
Explicitly list anachronistic text, logos, vehicles, street furniture, modern clothing, extra openings, changed rooflines, etc.

## 7. AI image prompt schema

Use:

**Purpose:** what this frame must communicate.

**Verified constraints:** evidence-backed scene facts.

**Subject invariants:** geometry/identity/costume/object details that cannot change.

**Composition:** shot size, camera angle, foreground/mid/background.

**Camera:** lens family, height, depth, perspective.

**Lighting:** time, direction, quality.

**Texture/style:** only after factual constraints.

**Negative constraints:** anachronisms, text errors, mutations.

**Reference policy:** which uploaded image controls what.

## 8. AI video prompt schema

For each shot:
- story purpose / director intent
- reference-role map (what each asset controls)
- start-frame description/reference
- end-state
- **one primary subject action**
- camera motion
- environmental motion
- duration
- speed/rhythm
- continuity constraints
- things that must stay still
- forbidden changes
- generation risk
- safer fallback preserving the same story function

Avoid “cinematic, epic, dramatic” as substitutes for action and camera instructions.

## 9. Animatic timing gate

Do not lock shot durations from the storyboard table alone. Build an animatic with:
- storyboard/keyframe frames
- scratch VO and **measured** read duration
- temporary music or rhythm map
- SFX/ambience
- silence beats
- actual transition durations

Revise the shot board after this pass. A beautiful static board that cannot carry the spoken line or musical turn is not production-ready.

## 10. Transitions with meaning

Prefer motivated transitions:
- shape match: gate arch → present arch
- gesture match: hand signing register → hand swiping student card
- sound bridge: bell/train/footsteps/turning page
- document dissolve into real location
- map line becomes road/path

Do not use transition effects simply for variety.

## 11. Shot-list regrouping

After story-order storyboard, create a production-order shot list grouped by:
- location/setup
- actor/costume
- prop
- time-of-day/light
- archival postproduction task
- AI-generation reference pack

For live/hybrid shots, also include lens, camera height/position, movement rig, blocking, lighting/depth, VFX/clean-plate needs, audio, and edit handles. This is the bridge from artistic storyboard to Techvis/execution.

This reduces reshoots and continuity errors.

## 12. Generation reproducibility

For AI-generated shots, maintain a structured generation record with:
- shot/prompt ID and prompt version
- provider/model/version or endpoint
- reference asset IDs and start/end frames
- duration/aspect ratio/FPS
- pose/depth/motion controls when used
- seed/randomness parameter when exposed
- generation date/operator/attempt number
- output asset ID/path
- approval status and reviewer note

A later editor should be able to identify exactly which attempt became the approved shot and rerun only the failed shot rather than reconstruct the entire sequence.

## v1.8 screenplay rule: causality before Flow units

For Google Flow projects, maintain two layers:

1. **Narrative scene** — carries a story turn, evidence, emotional/information change, and causal handoff.
2. **Flow generation unit** — a model-native 4/6/8/10-second production problem selected from the approved scene.

Do not make every narrative scene equal to one generated clip. A strong scene can combine Flow footage, archival evidence, deterministic motion graphics and post-produced narration.

Before final wording, create a causal map using `BEFORE -> TRIGGER/EVIDENCE -> BECAUSE/THEREFORE -> AFTER -> NEXT QUESTION`.

### Narration function test

For each VO line mark exactly one dominant function:
- FACT
- CAUSE
- CONSEQUENCE
- REFRAME
- QUESTION/PROMISE
- EMOTIONAL/HISTORICAL PERSPECTIVE

If the visual already supplies the FACT, prefer CAUSE / CONSEQUENCE / REFRAME rather than repeating the caption.

### Flow generation-language separation

Keep director/story notes in Chinese if that is the working language. The fields that compile to Google Flow should be concise English production language: one visible action, environment response, camera, timing and end behavior. Exact historical Chinese text remains a locked/post-production asset rather than generated typography.
