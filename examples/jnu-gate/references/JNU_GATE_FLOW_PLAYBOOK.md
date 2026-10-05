> Optional historical example material. Source IDs and earlier creative decisions are illustrative.
> Recheck historical claims independently; this file grants no production authorization.
> No private source media, live-provider validation or current competition logistics are bundled.

# 《门外，是四海》 — Google Flow Production Playbook

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

This file is project-specific. It assumes verified history/evidence remains authoritative and the current generator is Google Flow.

## 1. The film is not a sequence of Flow demos

Flow should serve the existing thesis:

**“门”从具体建筑，逐渐变成进入、离开、迁徙、坚持、重建与面向四海的阈限。**

Do not optimize individual Flow shots until the screenplay has a causal spine.

## 2. Recommended story logic

Do not treat this as mandatory chronology. Validate against the Evidence Ledger.

A strong causal scaffold is:

1. **Present threshold / question** — the current gate triggers the question: what did this institution have to pass through to arrive here?
2. **People enter before dates accumulate** — archival people make the institution human, not just architectural.
3. **A place takes shape** — gate/plan/campus evidence shows an institutional world forming.
4. **The line breaks** — a spatial/route rupture changes the meaning of “gate” from entrance to departure.
5. **Movement does not equal disappearance** — Jianyang evidence accumulates to prove continuity of school life.
6. **Return/rebuilding** — later evidence changes the motif again: the threshold can be rebuilt.
7. **Present gate payoff** — the modern gate now contains the memory/meaning of earlier thresholds rather than merely being the final chronological image.

Every sequence must have `BECAUSE / THEREFORE`, not merely `AND THEN`.

## 3. VO rules for this film

The narration should be precise, restrained, and image-aware.

Prefer:
- short clauses;
- concrete verbs;
- one claim per sentence;
- cause/effect or re-framing rather than image description;
- silence around visually strong evidence;
- exact dates only when the date itself changes the story.

Avoid slogan chains such as:
- “薪火相传、弦歌不辍、砥砺前行、声教四海” used as generic glue;
- repeating “暨南” in every sentence;
- “历史的车轮”“时代洪流” unless tied to a concrete verified event;
- narration that simply reads a visible date/title/photo caption.

### VO test

For every line ask:
1. If muted, can the image already say this?
2. If yes, does the VO add **why / consequence / meaning**?
3. Is every factual clause mapped to an Evidence ID?
4. Can the sentence be spoken naturally in one breath?

## 4. Flow micro-scenes for the gate motif

### Present gate — use Flow
Good Flow problem: controlled camera movement through a real/approved gate frame, subtle environment motion, a clean end state.

### Present gate -> historical gate — use Frames/occlusion, not free morph
Do not ask Veo/Flow to “transform the modern gate into the 1906 gate” if geometry/context are far apart.

Preferred:
- Phase A: move into a column/doorway/dark occlusion or composited paper layer.
- Reset/bridge.
- Phase B: emerge from the corresponding historical gate frame with matching direction.

### Nanjing archival group A089/A090/A091/A092 — mostly deterministic/composite
Use a precomposed archive-space frame or 2.5D layout. Flow can animate a **camera path through the already-designed composite**, but should not invent motion for the people in the photographs.

### Shanghai plan / route — deterministic line + selective Flow
Accurate map/route/date animation is better as motion graphics. Flow may generate a surrounding atmosphere or a camera transition, not the cartographic facts.

### Jianyang A176/A177/A184 — evidence accumulation
Primary route: deterministic evidence-wall/contact-sheet build. If using Flow, provide an approved composite frame and animate only the camera/paper depth/ambient layer. Historical people remain still.

### Present-day payoff — Flow hero shot
A carefully controlled present-day gate shot is a strong place to spend higher-quality Flow generation: the motion and final composition should pay off the opening rather than merely show a beauty shot.

## 5. Flow asset mapping for this project

Examples; replace with the actual Asset Bible IDs:

- `GATE-NOW` -> START_FRAME / ARCHITECTURE ingredient when current gate continuity matters
- `GATE-NJ-R` -> historical architecture reference; reconstruction status must stay explicit
- `GATE-SH-R` -> historical architecture reference
- `GATE-JY-R` -> historical architecture reference
- `GATE-GZ-R` -> historical architecture reference
- `A089/A090/A091/A092` -> POST/COMPOSITE archival evidence, not character Ingredients
- `A176/A177/A184` -> POST/COMPOSITE archival evidence
- verified gate signage -> POST_ONLY_TEXT / preserved pixels

Do not turn every archival photo into an Ingredient. Ingredients should anchor recurring identity/appearance, while evidence images often belong in deterministic composites.

## 6. Flow prompt examples for this project

### Example — present gate controlled move

```text
Wide-to-medium observational shot. The camera makes a slow, steady forward dolly along the central gate axis while leaves and distant campus activity move subtly in the background. Keep the architectural perspective stable and the motion restrained. The final two seconds decelerate into a centered, quiet threshold composition suitable for a cut into the archival sequence. Natural campus ambience, no dialogue.
```

### Example — archive composite camera move

```text
The supplied composite archival frame remains historically unchanged. No people inside the photographs move. The camera travels slowly through the layered paper depth, passing one foreground photo edge to reveal the next evidence layer. Only paper-layer parallax, shallow focus change and subtle ambient dust/light movement are visible. The final frame settles on the selected archival photograph for the next edit.
```

### Example — historical gate emergence after occlusion

```text
Beginning from the supplied historical gate frame, the camera continues the same forward screen direction established by the previous shot. It emerges gently from the foreground occlusion into a stable frontal view of the gate. No architectural deformation and no invented human action. The movement remains even and settles before the next archival cut. Restrained outdoor ambience only.
```

## 7. Script-to-Flow mapping rule

A narrative scene can contain:
- one Flow hero shot;
- one archival hold;
- one deterministic graphic;
- another Flow transition.

Therefore **do not require every row of the narrative script to become a Flow prompt**.

The scene script says what the audience experiences. The Flow unit plan says which pieces Flow should produce.

## 8. Flow audio policy for this project

Default:
- final historical narration: post-production VO;
- exact quotations/names: post-production VO;
- generated Flow audio: environmental ambience/SFX when helpful;
- no generated dialogue from archival people;
- music composed/licensed/controlled separately unless a temporary generated cue is explicitly disposable.

## 9. Director rejection rules

Reject/re-route a Flow shot if:
- it is visually impressive but does not advance the story state;
- the prompt requires two scene changes;
- a historical gate warps to hit an end frame;
- the film invents animation inside archival people;
- precise Chinese signage changes;
- the main effect could be more accurately created in 2.5D/motion graphics;
- a generated shot repeats the same slow push language without new meaning;
- three attempts fail for the same structural reason.

## v1.10 correction: film opening/ending ≠ Flow shot endpoints

For 《门外，是四海》, never use one global “first frame / last frame” pair as if it controls the whole generated film.

Use three separate systems:

- `05a_film_opening_ending.md`: whole-film visual question/payoff only.
- `05f_shot_endpoint_plan.md`: each individual Flow unit's Start Frame / End Frame / KEEP / CHANGE / PATH.
- carry frames: extracted only after a generated unit passes review.

### Example — opening gate sequence

Do not write:

```text
Film first frame = present gate
Film final frame = present gate after 120 years
therefore every generated shot should interpolate between them
```

Instead:

```text
SHOT A — START_FRAME
Start: approved present-day gate composition
End frame: optional
Goal: approach the gate threshold

SHOT B — FRAMES or START_FRAME
Start: tighter threshold composition from A / approved carry frame
End: near-full occlusion or dark threshold state
Goal: create a locally reachable transition state

CUT / RESET

SHOT C — START_FRAME
Start: approved archival threshold / historical gate composition
End: optional or local final composition
Goal: continue forward motion inside the historical visual world
```

The cross-era idea belongs to the **edit and sequence design**; each Flow clip only solves a local, reachable visual problem.

### Per-shot endpoint checklist

Before compiling each Flow prompt, answer:
- What exact image starts this clip?
- Does this clip truly need a supplied End Frame?
- If yes, is that End Frame a natural future state within this clip duration?
- What remains fixed?
- What changes?
- What is the physical path?
- Is the pair R-A/R-B, or does it really need a bridge/reset?
- If the shot succeeds, should a carry frame be extracted for the next unit?

### Archive clusters

For A089/A090/A091/A092 and A176/A177/A184, endpoint frames should usually be approved composites or layout states rather than raw model-invented arrangements. Flow may animate parallax, camera motion, paper-edge occlusion, or focus, while people, signage, dates, and documentary evidence remain fixed.
