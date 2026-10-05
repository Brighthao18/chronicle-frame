> Retained internal change notes, not reconstructed Git history or evidence of public releases.

# v3.2.1

Readiness patch: reject stale generated preview lineage and verify interrupted
picture-cache provenance. Adds three regression tests and a bounded live pilot
acceptance guide. No new provider integrations or claims of live validation.

# v3.2.0

Adds a canonical production graph, one-command local preparation, playable still-based animatics and transitive input freshness checks. Retains previous releases and their source-first human-gate boundaries.

# v3.1.0 — autonomous execution revision

The current entrypoint is `SKILL.md`. This release adds durable image/Flow execution, dependency and receipt checks, hash-bound review, adaptive retry and verified local finishing. Earlier release notes below are historical; the v3.1 entrypoint and execution references take precedence.

# Changelog

## 3.0.0

Automation-first production rebuild.

Added:
- four-gate human-in-the-loop architecture (`G1_STORY`, `G2_VISUAL`, `G3_HERO_MOTION`, `G4_PICTURE_LOCK`)
- capability broker and `pipeline_controller.py` state/next-action controller
- machine-readable Image 2.5 queue with best-of-N, risk and autonomy fields
- direct P2/P3 source-pixel re-overlay via `apply_locked_overlays.py`
- SHA256 media/asset registry via `register_asset.py`
- machine-readable Google Flow job queue via `compile_flow_jobs.py`
- HTML Flow operator fallback for environments without authenticated browser automation
- technical/endpoint/boundary QC and low-risk auto-promotion via `auto_qc_media.py`
- compact hero-only visual/motion contact sheets via `build_review_board.py`
- automation references for orchestration, human gates, Image 2.5, Flow and retry/QC

Changed:
- source-first production is the default for 《门外，是四海》; legacy AI-generated outputs are ignored unless explicitly imported
- Image 2.5 is used aggressively as the visual-state engine instead of being reserved for a few special composites
- routine low-risk stills and Flow shots no longer require manual per-item approval
- Flow execution should be automated through an authenticated browser/computer-use environment when available
- previous universal 10-second and fixed-reference assumptions are removed from v3 Flow planning
- approved Flow outputs live at `generated/flow_approved/<Unit>.mp4` for direct assembly
- failure handling routes to deterministic overlay/local edit/Omni edit/bridge/split before fresh rerolls

## 2.0.0

Seam-first production rebuild for 《门外，是四海》 and Google Flow.

Added:
- `references/STILL_ASSET_AND_SEAM_PIPELINE.md` — separates source-locked, code-composite, ChatGPT Image 2.5, hybrid, and post-graphic still routes
- `examples/jnu-gate/references/JNU_GATE_V2_PRODUCTION_BASELINE.md` — preserves the approved 35-shot / O1-F1 / S00-S09 baseline while treating fixed 10-second / three-reference rules as legacy assumptions
- v2 `references/providers/FLOW_SHOT_ENDPOINT_SYSTEM.md` with planned seam frames distinct from carry frames
- `03d_frame_asset_plan.md` — Start/End/Seam/Bridge asset contracts with P0–P3 pixel locks
- `05h_join_contracts.md` — `EXACT_SEAM / FLOW_EXTEND / MATCH_CUT / OCCLUSION_RESET / GRAPHIC_RESET / HARD_CUT`
- `scripts/compile_image25_jobs.py` for environments without direct image-tool execution
- `scripts/review_join_contracts.py`
- `scripts/compile_direct_assembly.py` producing generation queue + direct-assembly CSV/runbook
- `scripts/assemble_direct.py` to render a straight-cut ffmpeg picture master from approved manifest trims
- `scripts/upgrade_project_v20.py` additive project migration

Changed:
- ChatGPT Image 2.5 is the preferred generative still renderer, while evidence-critical source pixels/text remain source/code/post locked
- Flow is used primarily for motion between approved reachable states, not for recreating archive truth, typography or complex deterministic composites
- per-shot planning records final edit duration separately from Flow source duration; universal 10-second generation is removed as a default
- every important adjacent shot pair receives an explicit join contract before final generation
- carry frames are fallback post-generation handoff assets rather than the primary continuity design
- direct assembly is now a first-class target: incompatible joins should be redesigned upstream, not hidden with ad-hoc NLE dissolves

Project-specific effect for 《门外，是四海》:
- preserve the latest approved Animatic V1, O1/F1 anchors, S00–S09 and 35-shot story order
- convert approved static visual states into reusable mother frames and shared seam frames
- route archive/text/map precision to deterministic or hybrid Image 2.5 + code compositing
- use Flow Frames/Start Frame/Extend only where motion adds genuine cinematic value

## 1.10.0

Flow per-shot endpoint architecture correction.

Added:
- `references/providers/FLOW_SHOT_ENDPOINT_SYSTEM.md`
- `05a_film_opening_ending.md` for **whole-film** opening/ending only
- `05f_shot_endpoint_plan.md` for **single Flow shot** Start/End conditioning
- `05g_shot_endpoint_review.md` generated by `scripts/review_flow_endpoints.py`
- `scripts/review_flow_endpoints.py`
- `scripts/upgrade_project_v110.py`

Changed:
- Flow prompts are now compiled by joining `04c_flow_prompt_blueprints.md` with authoritative `05f_shot_endpoint_plan.md` rows
- `FRAMES` mode requires per-shot Start + End frame IDs; `START_FRAME` requires only the shot Start frame; `EXTEND` inherits the approved clip state
- carry frames are explicitly post-generation continuity assets, not planned shot end frames and not whole-film ending frames
- new projects no longer use `05a_anchor_frame_plan.md`; that legacy filename is retained only in upgraded projects for backward compatibility
- new Flow scene units no longer duplicate Start/End columns; endpoint state lives in `05f`
- Flow prompt lint parsing fixed so v1.10 compiled prompt blocks are actually detected and reviewed
- Flow projects use one final Flow prompt compiler, avoiding duplicate general-vs-Flow prompt packs

Project-specific effect for 《门外，是四海》:
- modern gate → historical gate is treated as multiple locally reachable shot endpoint problems rather than one whole-film or cross-era endpoint pair
- archival evidence walls and historical text remain deterministic/composite where precision matters

## 1.9.0

Flow prompt quality correction. Replaces v1.8 over-compressed motion-only defaults with balanced cinematic prompt blueprints. Adds mode-specific density bands, visual-premise retention, anchor-fact selection, natural-paragraph compilation, under-specification warnings, and project-specific Flow prompting guidance.


## 1.8.0

Google Flow-native screenplay and prompt upgrade for 《门外，是四海》.

Added:
- story causality map (`04a_story_causality_map.md`) using BEFORE -> EVIDENCE/TRIGGER -> BECAUSE/THEREFORE -> AFTER -> NEXT
- two-layer Flow screenplay (`04b_flow_scene_script.md`): narrative scenes separate from Flow generation units
- five-pass script review: Writer / Editor / Historian / Director / Narrator
- Flow reference-role plan (`03c_flow_reference_plan.md`) for Ingredients/Characters/Frames/post-only assets
- `references/providers/FLOW_NATIVE_SCREENWRITING_AND_PROMPTING.md`
- project-specific `examples/jnu-gate/references/JNU_GATE_FLOW_PLAYBOOK.md`
- Flow prompt compiler (`scripts/compile_flow_prompts.py`)
- Flow screenplay structural reviewer (`scripts/review_flow_script.py`)
- Flow prompt linter (`scripts/lint_flow_prompts.py`) for prompt length, conflicting camera axes, static-detail repetition, technical-parameter leakage, and over-sequencing
- non-destructive v1.8 upgrader with `--flow`
- Flow-aware QC and removal of the obsolete universal 3-reference assumption

Changed:
- Flow prompts are compiled from approved micro-scene fields rather than expanded from the whole screenplay
- final historical VO defaults to post-production; Flow native audio is optional ambience/SFX unless deliberate dialogue is needed
- Flow mode routing now distinguishes START_FRAME / FRAMES / INGREDIENTS / EXTEND / OMNI_EDIT / SKIP_FLOW
- 《门外，是四海》 archival evidence clusters are routed toward deterministic composite/2.5D treatment unless Flow adds genuine motion value

## 1.7.0

Reachability-first generation upgrade based on internal design notes on first/last-frame planning and AI-video prompt engineering.

Added:
- `references/ENDPOINT_REACHABILITY_AND_PROMPTING.md`
- `examples/jnu-gate/references/JNU_GATE_GENERATION_PLAYBOOK.md` dedicated to 《门外，是四海》
- `05d_endpoint_reachability.md` with R-A/R-B/R-C/R-D endpoint classes and AI-value routing
- `05e_bridge_keyframe_plan.md` for 40–60% bridge frames and occlusion resets
- `06d_generation_review.md` for candidate-level endpoint/boundary/motion/cuttability review
- `scripts/compile_generation_plan.py` — route-aware compiler that may emit I2V/FLF prompts, split bridge prompts, or deterministic edit recipes
- `scripts/lint_generation_prompts.py` — detects prompt overload, conflicting camera moves, excessive sequencing, negative-instruction sprawl, and archival-person motion risks
- `scripts/upgrade_project_v17.py` non-destructive upgrader

Changed:
- prompt design is motion-first and deliberately concise for I2V
- endpoints are checked for reachability before prompt writing
- R-C transitions default to bridge-frame splitting; R-D transitions default to occlusion/edit/composite rather than direct morphing
- the literal final frame is no longer automatically used as the next carry frame; boundary-snap review chooses the cleanest stable pre-snap frame
- hero transitions use a failure-dimension review loop; repeated same-dimension failure triggers constraint redesign instead of blind rerolls
- 《门外，是四海》 now routes many archival/map/evidence-wall shots to deterministic 2.5D/motion-graphics/editing instead of primary AI video generation

Retained:
- v1.6 chain compiler for backward compatibility
- v1.5 three-reference / ten-second constraint model
- v1.4 jnu_gate creative mode
- evidence ledger, animatic, anti-slideshow, and reproducibility layers
## 1.6.0

Automatic chained-prompt compiler upgrade.

Added:
- `scripts/compile_chain_prompts.py`
- slot-level `Ref1 / Ref2 / Ref3` planning in `05c_shot_chaining_plan.md`
- generated `06b_chain_prompt_pack.md` with copy-ready English I2V prompt blocks
- generated `06c_chain_generation_runbook.md` with sequential generate → review → extract → carry/reset operations
- `scripts/upgrade_project_v16.py` for non-destructive migration
- explicit carry-frame approval branch so bad tail frames do not propagate downstream
- 《门外，是四海》 slot-pattern guidance for gate passage, archive-border reveal, route continuation, and Jianyang evidence-wall accumulation

Strengthened:
- the 3-reference cap is now an explicit operator assignment, not a vague budget
- each compiled shot states its next-shot extraction rule and reset conditions
- composite-anchor strategy is preferred when the visual idea depends on more than three historical source assets

Retained:
- v1.5 shot chaining / max-10-second planning
- v1.4 creative-anchor and `jnu_gate` director mode
- v1.3 animatic / asset bible / reproducible generation pipeline

## 1.5.0

Constraint-aware AI-video organization upgrade.

Added:
- dedicated shot-chaining reference: `references/SHOT_CHAINING_AND_CONSTRAINTS.md`
- `05c_shot_chaining_plan.md` for extracted tail-frame continuity, reset points, and reference budgeting
- explicit support for workflows where the model allows **max 3 reference images per shot** and **max 10 seconds per generated clip**
- carry-forward strategy: generate/approve a shot, extract the cleanest tail or near-tail frame, and use it as the next shot's start anchor when beneficial
- composite-anchor strategy for shots that conceptually need more than 3 source assets
- non-destructive v1.5 upgrader: `scripts/upgrade_project_v15.py`
- QC awareness for chaining plans and real model limits

Strengthened:
- sequence design now connects more directly to generation boundaries and clip segmentation
- I2V prompting now records whether the next shot should inherit a carried frame
- initialization metadata now records AI generation constraints in `project.json`

Retained:
- v1.4 creative-anchor and `jnu_gate` director mode
- v1.3 asset bible / animatic / reproducible generation pipeline
- evidence ledger / reconstruction safeguards / anti-slideshow logic

## 1.4.0

Creative-anchor and project-specific director upgrade based on internal creative design notes.

Added:
- layered creative system: strategy -> divergence -> convergence -> anchor -> motion -> validation
- mandatory first/final-frame planning for substantial short films
- attention/state-change map for 3–5 minute judged films
- I2V motion-only prompt grammar (`SUBJECT / ENVIRONMENT / CAMERA / TIMING / END STATE`)
- Creative QA and controlled one-variable variant testing
- dedicated `jnu_gate` profile for 《门外，是四海》
- project-specific creative lab, asset/motif relationship graph, anchor-frame laboratory, sequence hypothesis, sound/motion grammar, and director review
- non-destructive v1.4 upgrader and gate-specific QC

Retained:
- evidence ledger / reconstruction safeguards
- v1.2 anti-slideshow sequence-first synthesis
- v1.3 asset bible / animatic / reproducible generation pipeline

## 1.3.0

Production-readiness upgrade based on the 2026-09-09 AI storyboard/video workflow research report.

Added:
- Asset / Style Bible with stable IDs and approval states
- Production storyboard schema with director intent, lens feel, camera position, one primary action, generation risk and safer fallback
- Animatic gate with measured scratch VO, temporary music/rhythm, SFX and revised durations
- model-neutral master prompt -> model-specific adapter workflow
- reference/image-to-video default for continuity-sensitive narrative work
- multi-model bake-off guidance for difficult shots
- structured generation manifest and attempt log for reproducibility
- live/hybrid technical shot-list handoff
- cloud-data-boundary/privacy guidance
- non-destructive project upgrader from v1.2-or-earlier
- expanded QC for production readiness and reproducibility

Retained and strengthened:
- evidence ledger and historical reconstruction policy
- sequence-first visual synthesis and anti-slideshow QC
- Chinese planning + English production prompt policy
