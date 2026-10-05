# Historical Short Film QC Rubric

## Fatal / readiness gates

A film cannot be called ready if any is true:
- unverified material claim appears as fact
- fabricated quotation is presented as authentic
- AI reconstruction is represented as archival evidence
- runtime exceeds the hard ceiling
- official submission requirement is unmet
- core story depends on an unavailable asset with no replacement
- rights/consent issue is knowingly unresolved for a required public asset
- the project claims **generation-ready** while continuity-critical assets are not frozen/approved
- the project claims **generation-ready** while required sequences have not survived an animatic timing pass
- final AI shots are required but there is no way to identify the prompt/reference/model attempt that produced the approved result

## Scored rubric — 100 points

| Dimension | Points | What earns full marks |
|---|---:|---|
| Historical integrity | 18 | Claims traceable; uncertainty handled; reconstruction not confused with evidence |
| Narrative specificity | 13 | One clear carrier/question; not a generic chronology |
| Emotional architecture | 8 | Emotion changes because of concrete events/images rather than generic music |
| Visual storytelling | 15 | Sequence-first design; assets interact; motion/cuts express relationships; no slideshow logic |
| Originality / memorability | 8 | Distinct motif and cinematic mechanism, not publicity-template language |
| Script economy | 8 | Every line/beat earns time; visual breathing room remains |
| Production storyboard / continuity | 10 | Each shot is observable; one primary action; lens/position/action/continuity/reference/fallback are explicit |
| Animatic + sound timing | 7 | Scratch VO measured; temp music/rhythm tested; silences and transitions timed |
| AI reproducibility / generation control | 5 | Approved asset IDs; prompt/model/reference/attempt logging; failed shots independently rerunnable |
| Production feasibility | 3 | Assets, post tasks, generation burden and fallbacks are realistic |
| Brief / competition fit | 5 | Hard requirements satisfied; format appropriate |

Suggested readiness bands:
- 90–100: competition/production-ready after final technical check
- 80–89: strong; revise top weaknesses
- 70–79: concept works but structural/production problems remain
- <70: reframe before polishing

A high score cannot override a fatal/readiness gate.

## Adversarial questions

### History
- Which sentence would a historian challenge first?
- Which image could mislead viewers about what is authentic?
- Have we used a later photograph to imply an earlier event?

### Story
- What exactly changes from beginning to end?
- If 30% must be cut, what stays? If that is unclear, the spine is weak.
- Is the film about a particular story or merely covering a topic?

### Visuals
- Was each major sequence designed around a visual engine before individual assets were assigned?
- Are there three consecutive beats whose only visual logic is “show another old photo” or “same photo with another slow push/pan”? If yes, fail visual QC until redesigned.
- In each major sequence, do multiple relevant assets interact, or is there a strong reason for a single-source hold?
- Are adjacent sequences using different primary visual engines rather than cosmetic angle changes?
- Does the cut itself express a relationship: shape, gesture, word, geography, cause, rupture, or sound?
- Does every generated narrative shot have one primary action rather than several unrelated actions packed together?
- Can a crew member execute each shot description without guessing lens feel, camera position, action, transition, or continuity anchors?

### Asset / continuity state
- Are recurring characters, gates, documents, costumes, props and environments assigned stable IDs?
- Which approved reference controls identity? Which controls geometry? Which controls finish?
- Has any later shot silently changed a building, costume, object state, screen direction, season, or light direction?

### Animatic / sound
- Has the narration been read at actual pace, or only estimated by word count?
- Does temporary music support the visual turns instead of dictating false emotion?
- Where should silence/ambient sound replace narration?
- Do J-cuts/L-cuts or sound bridges improve transitions?
- Which shot durations changed after the animatic test?

### AI generation
- Is the shot better routed through approved keyframe -> I2V/reference-to-video rather than free T2V?
- What is the safer fallback if the preferred shot fails after repeated attempts?
- Is the result editable and repeatable, or merely spectacular?
- For a high-risk shot, would a multi-model bake-off reduce uncertainty?
- Can we identify provider/model/version, prompt version, references, attempt number and approved output?

### Ending
- Does the last image complete the opening question/motif?
- Would the ending still work without a slogan?

## Deliverable checklist

- [ ] 00_brief.md
- [ ] 01_evidence_ledger.md
- [ ] 02_angle_matrix.md
- [ ] 03_story_bible.md
- [ ] 03_asset_style_bible.md
- [ ] 04_script.md
- [ ] 05_storyboard.md
- [ ] 05_animatic_plan.md
- [ ] 06_ai_prompts.md (when AI is used)
- [ ] 06_generation_manifest.json (when AI is used)
- [ ] 06_generation_log.csv (when AI is used)
- [ ] 07_shot_list.md
- [ ] 08_asset_manifest.md
- [ ] 09_edit_plan.md
- [ ] 10_qc_report.md


## v1.7 generation-readiness gate

Before approving a shot for generation, verify:
- endpoint reachability class exists;
- AI-value judgment exists;
- production route is appropriate;
- R-C/R-D shots have bridge/occlusion/reset or deterministic edit logic;
- start frame is a clean motion-start state;
- end frame is a natural reachable future state;
- prompt is motion-first and not overloaded;
- first/last 10% boundary behavior is reviewed after generation;
- a carry frame is exported only from a stable cuttable region.
