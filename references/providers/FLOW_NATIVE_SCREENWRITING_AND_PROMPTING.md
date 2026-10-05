# Google Flow Native Screenwriting & Prompting

Use this reference when the active generator is **Google Flow**. Flow capabilities, model labels, credit costs, and exact duration/reference limits can change; verify the current project UI before final generation. Do not hard-code yesterday's model constraints into the story.

## 1. Flow is a shot-production environment, not the screenplay itself

For a multi-minute historical film, keep two different time scales:

1. **Narrative scene / sequence** — usually 15–35 seconds; carries one story turn, question, or emotional movement.
2. **Flow generation unit** — usually one model-native 4/6/8/10-second clip (exact choices depend on the active Flow model).

Do not rewrite the story so every narrative beat is exactly eight seconds. Instead, split an approved scene into only the Flow units that genuinely need generation.

## 2. Script pipeline: story first, Flow second

Use this order:

`intent -> causal beats -> scene script -> visible actions -> Flow units -> references/frames -> prompt -> generation`

### Causal beat test

Every major beat should answer:
- What is the viewer asking/believing before this beat?
- What evidence/event enters?
- What changes because of it?
- What emotional state changes?
- Why does the next beat follow from this one?

If the answer is only “now show another old photo / another date,” the screenplay is chronological coverage, not a story.

## 3. Screenplay is a multimodal production spec

For each narrative scene record:
- scene purpose / story turn
- before-state and after-state
- visible action or visual proof
- narration/dialogue function
- exact narration/dialogue text if locked
- SFX / ambience / music function
- on-screen text that must be added deterministically in post
- evidence IDs
- transition / causal handoff
- production route: `FLOW / ARCHIVAL_EDIT / MOTION_GRAPHIC / LIVE / COMPOSITE / MIXED`

A line of VO must perform one of these jobs:
- reveal a fact not already obvious in the image;
- explain causality;
- reframe the meaning of what we see;
- connect distant evidence;
- create a question/promise;
- provide emotional or historical perspective.

If it merely names what is already on screen, cut or rewrite it.

## 4. Five-pass script review

Do not ask one model pass to optimize everything at once.

### WRITER pass
Only inspect premise, causality, escalation, turn, payoff, motif evolution, emotional movement.

### EDITOR pass
Only inspect redundancy, chronology overload, repeated facts, runtime, VO density, whether each scene earns its place.

### HISTORIAN pass
Only inspect evidence status, exact wording, chronology, quotation/proper-name accuracy, reconstruction labeling.

### DIRECTOR pass
Only inspect whether each scene can be expressed through observable images/actions and whether the proposed production route is feasible.

### NARRATOR / ACTOR pass
Read dialogue/VO aloud. Flag bureaucratic syntax, long subordinate clauses, slogan chains, unnatural emphasis, and names/terms requiring pronunciation notes.

Do not merge all five passes into one vague “improve the script” instruction.

## 5. Flow reference system

Map approved project assets into Flow roles rather than repeatedly redescribing them.

Possible roles:
- `INGREDIENT_CHARACTER`
- `INGREDIENT_OBJECT`
- `INGREDIENT_ARCHITECTURE`
- `INGREDIENT_STYLE`
- `START_FRAME`
- `END_FRAME`
- `CARRY_FRAME`
- `COMPOSITE_FRAME`
- `POST_ONLY_TEXT`

Reference hygiene:
- use simple/isolated reference images when possible;
- avoid unrelated people/objects in an Ingredient;
- keep recurring references in a similar look & feel;
- state which visual fact each reference controls;
- do not ask prompt text to contradict the supplied frame/reference.

For historical Chinese signage, newspaper text, dates, maps, and exact captions: preserve verified pixels or add them in post. Do not make generated typography carry factual accuracy.

## 6. Flow mode routing

Choose a Flow capability based on the shot problem, not novelty.

### START-FRAME / IMAGE-TO-VIDEO
Use when an approved first frame already fixes subject, architecture, composition, light, and style. Prompt mainly describes motion.

### FRAMES-TO-VIDEO / FIRST+LAST
Use when the final composition is important **and the endpoints are reachable**. Describe the causal path; do not restate two still images.

### INGREDIENTS / CHARACTERS
Use when the same person/object/architecture/style must recur across shots. Ingredients are identity/appearance anchors; they do not replace a clean start frame when composition matters.

### EXTEND
Use when the approved clip should naturally continue its existing motion/state. Do not use Extend to solve a conceptual scene change that should be a cut/reset.

### SAVE FRAME -> NEW START/INGREDIENT
After approval, a stable frame may become the next shot's start/reference. Prefer a clean, cuttable frame, not automatically the literal final frame.

### OMNI EDIT / conversational edit
Use for a localized correction when the base clip is good enough to preserve. Do not keep conversationally patching a fundamentally unreachable motion path.

### SCENEBUILDER
Use for ordering, trimming, previewing, and assembling generated units. Scenebuilder is an editorial layer; it does not repair weak story causality.

## 7. Flow prompt principle: reference tells “what”; prompt tells “what happens”

For I2V/Frames workflows, the final prompt should be **shorter than the director notes**.

Do not paste the whole Story Bible into Flow.

### Flow prompt core

`cinematography + one visible action/path + environment response + timing + end behavior + optional audio`

Keep camera motion to one dominant trajectory, occasionally one secondary adjustment.

Avoid:
- “cinematic, epic, emotional, dynamic camera” without observable instructions;
- repeating every static feature already fixed by the frame/Ingredient;
- multiple scene changes inside one clip;
- long negative-prompt dumps copied from diffusion image workflows;
- generated exact historical text.

## 8. Flow prompt intermediate representation

Before writing the paste-ready English prompt, store a structured scene card:

```text
FLOW_UNIT_ID:
NARRATIVE_SCENE:
STORY_FUNCTION:
MODE:
DURATION_OPTION:
START_FRAME:
END_FRAME:
INGREDIENTS:
VISIBLE_START_STATE:
ONE_PRIMARY_ACTION:
ENVIRONMENT_RESPONSE:
CAMERA:
TIMING:
END_BEHAVIOR:
AUDIO_POLICY:
SFX/AMBIENCE:
DIALOGUE_IF_ANY:
CONTINUITY_LOCKS:
POST_ONLY_ELEMENTS:
FAILURE_RISK:
FALLBACK:
```

Then compile to Flow English.

## 9. Paste-ready Flow English prompt templates

### A. Start-frame / I2V

```text
{shot size / camera starting behavior}. {One primary visible action}. {Only necessary environmental response}. {Timing/pace}. The camera {one controlled trajectory}. The motion remains continuous and physically plausible, then settles into {end behavior/composition}. {Optional ambience/SFX only if intentionally generated.}
```

Do not repeat clothing, gate geometry, palette, lighting, or archival layout already defined by the source frame unless the model keeps violating a specific invariant.

### B. First + last frame

```text
Continuous single shot. Beginning from the supplied first frame, {causal movement path}. {Environment response}. The camera {trajectory}, with even speed and coherent parallax. The transition develops progressively rather than morphing abruptly, and naturally arrives at the supplied final frame. {Optional audio.}
```

If the two frames require too many simultaneous changes, do not make this prompt longer. Add a bridge frame or split the shot.

### C. Ingredient-guided shot

```text
Use the supplied Ingredients as identity/appearance anchors. {One primary action}. {Camera}. {Environment motion}. Keep the recurring subject/object/architecture visually stable while only the requested action/state changes. End on {observable state}.
```

### D. Extend

```text
Continue the existing shot seamlessly. Preserve the current camera direction, subject state, lighting and spatial continuity. {One next action / continuation}. {Environment response}. The motion remains consistent with the previous clip and settles on {next edit point}.
```

## 10. Audio policy for historical films

Flow/Veo can generate native audio, but production reversibility matters.

Default for evidence-heavy historical films:
- **final narration/VO:** generate or record separately in post;
- **precise quotations/names:** post VO unless native pronunciation has been verified;
- **ambience/SFX:** Flow generation may be used when useful;
- **music:** preferably controlled as a separate editorial layer;
- **lip-synced dialogue:** use only when dramaturgically necessary and technically tested.

This avoids re-generating a visually good shot because one historical name or sentence was pronounced incorrectly.

## 11. Flow-specific prompt QA

Before generation verify:
- prompt language is production-ready English unless the selected current model demonstrably benefits from another language;
- one primary action;
- one dominant camera path;
- event count fits the selected duration;
- no scene cut is hidden inside the prompt;
- static appearance is mostly delegated to frames/Ingredients;
- exact text/logo/map is marked post-only;
- end state is observable and reachable;
- audio is intentional and separated by function;
- prompt and references do not contradict each other.

After generation review:
- prompt adherence;
- subject/architecture/reference fidelity;
- first 10% boundary;
- last 10% boundary;
- motion/camera obedience;
- temporal flicker / geometry drift;
- audio correctness if used;
- cuttability;
- whether a clean frame should be saved as a new Ingredient/start frame.

## 12. Cost-aware exploration without creative compromise

Flow model labels/credit costs change; verify in the current UI. General production rule:
- explore story/motion with cheaper/faster modes;
- lock references, endpoint design and prompt before expensive final attempts;
- do not assume a higher-cost model will repair an unreachable shot design;
- save all successful frames/Ingredients and generation notes for reuse.

## v1.10 architecture note: endpoint planning is shot-level

Do not use the whole film's opening/ending design as a conditioning plan for intermediate Flow shots.

After Flow generation units are selected:
1. keep story-level opening/ending in `05a_film_opening_ending.md`;
2. plan each Flow unit's Start/End conditions in `05f_shot_endpoint_plan.md`;
3. only after a generated unit passes review may a carry frame be extracted for the next unit;
4. compile the Flow Prompt by joining `04c_flow_prompt_blueprints.md` + `05f_shot_endpoint_plan.md`.

For `FRAMES`, the two supplied endpoint images are the A/B visual states. The Prompt should primarily describe the path, timing, camera behavior, and invariants that connect them.
