# AI Video Production Pipeline: From Board to Reproducible Shots

This reference turns a storyboard into a controllable AI-video production package. It is intentionally separate from story design: a beautiful board is not yet a production-ready board.

## 1. Maturity ladder

A project should move through these gates in order:

1. **Story decision** — premise, evidence, emotional arc.
2. **Asset/Style Bible** — approved identities and invariants.
3. **Sequence design** — visual engine and editorial logic.
4. **Production storyboard** — shot-level camera/action/sound/continuity.
5. **Animatic** — timed boards + scratch VO + temp music/SFX.
6. **Generation test** — low-cost/low-resolution motion tests.
7. **Approved-shot generation** — only locked shots go high quality.
8. **Edit + sound + titles** — assemble and refine.
9. **Continuity/compliance QC** — historical, visual, technical, rights.

Do not jump directly from a prose script to expensive final video generation for narrative work unless the user explicitly wants rapid concept exploration.

## 2. Asset/Style Bible before bulk boards

Create `03_asset_style_bible.md` before generating many frames.

Use stable asset IDs rather than repeatedly redescribing assets in free text:

- `CHAR###` — character/person identity or reenactment performer
- `COSTUME###` — clothing/hair/accessory state
- `PROP###` — recurring prop
- `ARCH###` — architecture/building/gate
- `ENV###` — location/environment
- `DOC###` — document/newspaper/map/letter
- `STYLE###` — visual treatment / finish
- `AUDIO###` — approved music, ambience, archive audio, voice
- `REF###` — general reference pack

Each asset record should include:
- source/provenance
- historical status
- rights/permission
- approved reference file(s)
- identity invariants
- mutable fields
- forbidden mutations
- current approval state: `DRAFT / REVIEW / APPROVED / REJECTED`

**Rule:** once an asset is APPROVED, prompts should reference its ID and describe only the new action, framing, or lighting change for that shot unless an override is intentional.

## 3. Production storyboard is stricter than concept art

Each shot must specify:

`Shot ID | duration | purpose | director intent | shot size | lens feel | camera height/position | camera movement | ONE primary subject action | emotion | composition/depth | lighting | references | dialogue/VO | music/SFX | transition | continuity anchors | evidence IDs | generation risk | safer fallback`

### One-primary-action rule

Generative video is more controllable when one shot asks for one principal action.

Bad:
> The student walks through the gate, looks back, opens a letter, smiles, the camera cranes up, then the scene becomes 1907.

Better:
- Shot A: walk through gate.
- Shot B: stop and look back.
- Shot C: insert of letter opening.
- Shot D: transition through archival texture.

A shot may contain ambient secondary motion, but it should have one editorially dominant action.

## 4. Duration defaults are starting points, not laws

Use these as production defaults:

- hook/action insert/detail: ~0.5–1.5 s
- ordinary action/reaction: ~2–4 s
- dialogue/explanation/emotional build: ~3–6 s
- establishing/atmosphere/intentional historical hold: ~5–8+ s

For AI-generated narrative shots, prefer **3–6 second replaceable units** even when a model supports longer generations. Longer generated clips should have a clear reason and a simple action structure.

## 5. Animatic is a required decision gate

Create `05_animatic_plan.md` before calling the board locked.

The animatic plan must include:
- actual shot durations
- storyboard frame or approved keyframe per shot
- scratch VO text and measured duration
- temporary music cue(s)
- SFX/ambience cue(s)
- beat markers: hook / reveal / rupture / midpoint / climax / ending
- intentional silence
- transition timing
- shots that need more/less time after audio testing

### Scratch VO pass

Do not estimate final pacing from word count alone. Record or simulate a temporary read and log measured duration. Adjust visuals to the voice rather than forcing narration into preselected shot lengths.

### Temp music pass

Do not wait until final edit to discover the music rhythm. Use temporary music or a rhythm map during the animatic so that major visual turns and cuts can be tested against sound.

### Animatic approval states

- `BOARD_DRAFT`
- `ANIMATIC_V0`
- `ANIMATIC_REVISE`
- `ANIMATIC_APPROVED`

Do not describe a project as generation-ready until the relevant sequence is `ANIMATIC_APPROVED`, unless the user explicitly requests experimentation before lock.

## 6. Image-first vs text-first routing

For narrative, historical, advertising, character, architecture, product, or continuity-sensitive work:

**Default:** `Storyboard/approved keyframe -> Image-to-Video / Reference-to-Video`.

Use direct Text-to-Video mainly for:
- atmosphere/B-roll
- abstract transitions
- visual exploration
- effects where identity/geography continuity is low priority

For archival/historical work, a user-supplied or approved reference should normally control geometry and identity more strongly than free-text style language.

## 7. Model routing: choose by control need, not brand loyalty

Do not hard-code one platform as universally best. Before model-specific advice, verify current capabilities if web access exists.

Route by need:

### A. Storyboard / collaboration / approval layer
Use a storyboard/previs system when the main need is scene/shot organization, client review, versioning, animatic, or shot-list export.

### B. General high-quality video generation
Use a cinematic image/video platform when the need is broad T2V/I2V/V2V capability, camera experimentation, motion generation, or API workflows.

### C. Multi-reference consistency
Prefer systems with strong reference-to-video or multi-reference support when character, architecture, object, or costume continuity is critical.

### D. Multi-shot native generation
Native multi-shot features may be useful for concept exploration, but production editing should still preserve shot-level control and replaceability. Do not let a long native multi-shot clip erase editorial control.

### E. Local/private pipeline
Use local node-based/open-model workflows when confidentiality, reproducibility, custom ControlNet/pose/depth/LoRA, or unlimited low-cost iteration matters more than ease of use.

### Multi-model bake-off
For important/high-risk shots, create 2–4 model-specific variants when budget permits. Compare **usable-shot rate, continuity, motion fidelity, artifact rate, retries, and cost**, not only single-frame beauty.

## 8. Generation-ready shot package

Every AI shot should have:

### Core
- `shot_id`
- `prompt_id`
- `duration_seconds`
- `aspect_ratio`
- `fps_target`
- `primary_action`
- `camera_instruction`
- `start_frame_reference`
- `end_frame_reference` when useful
- `reference_asset_ids`
- `continuity_anchors`
- `negative_constraints`
- `evidence_ids`

### Optional control inputs
- pose reference
- depth map
- edge/line reference
- motion reference/video
- character reference
- environment reference
- style reference
- first/last frame control

### Reproducibility
- provider/model
- model version or endpoint
- seed/randomness parameter when exposed
- generation date/time
- generator/operator
- prompt version
- reference file hashes or stable file IDs when practical
- attempt number
- output asset ID/path
- status and reviewer note

Store structured records in `06_generation_manifest.json` and attempt notes in `06_generation_log.csv`.

## 9. Failure-aware prompting

Every difficult shot gets:

1. **preferred version** — the desired cinematic solution.
2. **safer fallback** — a simpler shot that preserves story function if the preferred generation is unstable.

Typical simplifications:
- wide complex action -> medium single action + cutaway
- moving crowd -> locked environment + foreground object motion
- long face performance -> shorter 3/4-face beats
- impossible archival animation -> composited document/geometry transition
- elaborate transformation -> explicit start frame + explicit end frame + shorter bridge

Never spend repeated generation budget defending a shot whose story function can be achieved more simply.

## 10. External continuity state

Long-form consistency must live outside the model.

Maintain:
- character state
- costume state
- prop state
- architecture/environment state
- screen direction
- time/weather/light state
- what has already happened in the story

A later shot must not silently resurrect a removed object, change a gate geometry, reverse travel direction, or change costume unless the story specifies it.

## 11. Low-cost validation before final generation

Recommended economy:

`static storyboard -> low-resolution animatic -> low-cost motion test -> approved shot -> final-quality generation -> edit`

Only reroll failed shots. Do not regenerate an entire sequence when one shot is the problem.

## 12. Definition of generation-ready

A sequence is generation-ready only if:
- story and evidence are stable;
- approved asset/style references exist for continuity-critical elements;
- every shot has one primary action;
- shot duration has survived the animatic/scratch-VO test;
- transitions are editorially motivated;
- difficult shots have a fallback;
- generation parameters can be logged and reproduced as far as the model allows;
- rights/privacy constraints for uploaded references are acceptable.

## 13. Live-action / hybrid Techvis handoff

When a storyboard will be shot with a camera, generate a technical shot list after artistic approval. Include as relevant:
- lens/focal length
- camera height and exact side of axis
- tripod/gimbal/dolly/crane/handheld rig
- actor/blocking path
- lighting direction / fixture role
- intended depth of field
- clean plate / VFX plate / tracking marker needs
- extra handles before/after action for editing
- safety/access constraints

The artistic storyboard says **why/what**; the technical shot list says **how to execute it**.

## 14. Data boundary before cloud generation

Before uploading real-person images, unreleased institutional material, private interviews, internal documents, or sensitive reference assets to a cloud generator:
- confirm the user has the right/permission to use the material;
- verify the provider's current retention/training/privacy policy when it matters;
- avoid assuming a consumer product has a no-training guarantee;
- prefer enterprise/no-training terms or local/private workflows for sensitive material when appropriate;
- record the chosen data boundary in the project brief or asset manifest.

Do not let model convenience silently override privacy, consent, or archival restrictions.

## v1.5 practical model-limit note

When the user's current video model allows only **3 reference images per shot** and **up to 10 seconds per clip**, treat those as first-class production constraints.

- break continuity-sensitive material into linked 2–6 second clips whenever possible;
- reserve one reference slot for a carried continuity frame when chaining is beneficial;
- use approved composite anchor frames when a shot conceptually depends on more than three source assets;
- log extraction rules and reset conditions so the edit does not collapse if one generated shot fails.


## v1.7 endpoint reachability gate

Before AI generation, classify endpoint burden and choose the route. A beautiful start/end pair that is not locally reachable is a production defect, not a prompt-writing challenge.

For first/last-frame or end-target clips, review the first and last 10% separately. Do not export a literal final frame when the model snaps into the endpoint; use a clean stable pre-snap frame or reset.

For hero transitions, generate about 3 candidates when practical. Repeated same-dimension failure means endpoint/path/reference/route should change before further rerolls.
