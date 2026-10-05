# Layered Creative System for AI Short Films

Use this reference when the project needs stronger concept generation, **whole-film** opening/ending design, retention logic, motion prompting, or pre-release creative QA. Per-shot Flow first/last-frame conditioning is handled separately in `FLOW_SHOT_ENDPOINT_SYSTEM.md`. It adapts internal project design decisions to evidence-grounded historical and institutional short films.

## 1. Do not treat AI filmmaking as one prompt

Default pipeline:

`Brief -> divergent concept matrix -> critical convergence -> time-coded narrative -> whole-film opening/ending -> sequence/shot design -> per-shot endpoint system -> I2V/Flow motion briefs -> animatic -> generation -> creative QA -> controlled variant test -> reusable learnings`

The creative problem is divided into five layers:

1. **Strategy** — who is watching, what should they understand/feel, and why this film exists.
2. **Concept** — conflict, emotional entry, narrative mechanism, and visual mechanism.
3. **Narrative** — second-by-second/beat-by-beat reason to continue watching.
4. **Film-level visual arc** — whole-film opening image, whole-film ending image, asset/style bible, key states. Shot-level endpoints are a separate generation-control layer.
5. **Motion/edit** — what moves, how the camera moves, timing, sound, transitions, and final assembly.

A project may be visually beautiful and still fail if these layers are not aligned.

## 2. Diverge first, converge second

Do not ask for “10 more similar ideas.” Force mechanism diversity.

Build a matrix using at least four axes:

`audience tension x emotion x narrative mechanism x visual mechanism`

Useful emotional entries:
- curiosity
- surprise
- empathy
- aspiration/pride
- loss/rupture
- belonging/identity

Useful narrative mechanisms:
- unanswered question
- mistaken expectation corrected
- object-led journey
- threshold/route journey
- micro-story
- before/after contrast
- accumulation of evidence
- repeated motif with changing meaning

Useful visual mechanisms:
- impossible but clearly metaphorical composite
- match geometry
- match motion
- archive-space traversal
- map-to-world transformation
- foreground occlusion transition
- split-time composition
- document-to-environment transformation
- repetition with escalation
- first/last-frame rhyme

### Two-pass rule

**Pass A — Divergence:** generate multiple concepts and forbid ranking.

Each concept must state:
- hook image
- central question
- emotional engine
- narrative mechanism
- visual mechanism
- evidence burden
- production risk
- why it is genuinely different from the others

**Pass B — Creative Director critique:** attack the concepts, identify cliché/convergence, combine only complementary mechanisms, and then score.

### Historical competition concept score

For historical/anniversary competition work, use this adapted 100-point score:

- 15 Hook / first-image power
- 20 Historical meaning + evidence strength
- 15 Emotion
- 20 Showability / visual storytelling
- 15 Originality / motif coherence
- 15 Feasibility / AI + edit risk

An evidence-fatal concept cannot win by score.

## 3. The first frame is a visual proposition

The opening frame is not merely a nice establishing shot. It should answer:

1. What am I looking at?
2. Why is it unusual, unresolved, or emotionally charged?
3. What question or promise makes the next shot necessary?

For judged historical films, avoid platform-clickbait language. Prefer a **visual contradiction, historical question, human detail, or impossible-but-obviously-metaphorical relationship**.

### First-frame contract

Define:
- single focal point
- visual anomaly/tension
- historical or thematic proposition
- information withheld
- first sound
- first cut/transition target

Create at least **3 opening variants** before locking a major competition film when time permits. Change one dominant mechanism at a time.

## 4. The final frame must transform the opening

The last frame should do at least one of:
- answer the opening question;
- transform the meaning of the opening object/motif;
- return to the opening composition with new information;
- leave an emotionally resolved open horizon;
- form a deliberate loop only when the loop serves meaning.

Do not default to a logo/title card as the emotional ending. Credits/disclosure may follow the actual payoff.

### Anchor-pair test

Place first and final frames side by side. Without narration, ask:
- Is there a visible relationship?
- Has the motif changed meaning?
- Does the ending feel earned by the film between them?

## 5. For each generated shot, anchor visual state before motion

For continuity-sensitive work, solve the still frame first:
- identity
- geometry
- composition
- lighting
- texture/style
- historical text/signage

Then decide whether this **individual shot** needs an explicit end state/frame. Only when an End Frame materially improves control should the model receive both endpoints. The whole-film ending is unrelated to this technical choice.

Default shot package:
- approved start frame
- optional/required approved end frame
- reference asset IDs
- one primary action
- motion-only brief
- continuity locks
- negative constraints

## 6. Separate visual prompts from motion prompts

For Image-to-Video, do not waste the prompt redescribing visual facts already fixed by the input image/reference.

Preferred motion schema:

```text
SUBJECT MOTION:
ENVIRONMENTAL MOTION:
CAMERA MOTION:
TIMING:
END STATE:
```

Historical archival rule:
- if real people are frozen in a historical photograph, `SUBJECT MOTION` is normally `none / preserve exact pose`;
- obtain motion from camera, layered parallax, foreground occlusion, paper/graphic layers, environmental effects that are defensible, or the transition itself;
- never animate a historical person's expression/body merely because the model can.

For Text-to-Video, visual description and motion both need specification because there is no approved source frame.

## 7. One shot = one dominant action, but one sequence = a designed progression

A 2–6 second AI generation is usually more replaceable than one long complex clip. The exact duration is artistic, not a law.

Every shot asks one main motion question. Every sequence asks a larger story question.

Bad shot:
> Student walks, turns, opens a letter, smiles, camera cranes, scene transforms to 1907.

Better editorial design:
- walk/threshold
- glance/reaction
- insert/document
- transformation/transition

The creativity should live in how shots connect, not in asking one generation to perform six events.

## 8. Retention is narrative causality, not frenetic cutting

For competition/docu-historical shorts, adapt short-form retention thinking rather than copying social-ad pacing.

Use an **attention map**:
- opening contract: what question is created?
- information gap: what is still unresolved?
- state change: what new visual/information/emotional state appears?
- turn: where is the viewer's prediction corrected?
- payoff: when is the opening promise fulfilled?

As a default diagnostic, every 20–30 seconds in a 3–5 minute film should produce a meaningful change in at least one of:
- historical question
- location/time
- evidence type
- visual engine
- sound state
- emotional direction

Do not insert random visual noise just to meet a cadence.

## 9. Story Editor pass before storyboard lock

Run a harsh critique pass:
- What does the viewer understand in the first 3–8 seconds?
- Where is the first information gap?
- Which narration line can become image/action?
- Where will attention likely sag?
- Is the turn a real change in understanding or only new wording?
- Does the payoff answer the opening?
- Are any generated actions technically over-complex?
- Does a beautiful shot fail to advance the story?

Return:
1. problems only;
2. minimum-change fix;
3. one bolder/higher-risk alternative.

## 10. Creative QA before expensive final generation

Use a 100-point pre-release score for major projects:

| Dimension | Weight | Question |
|---|---:|---|
| Opening proposition / hook | 15 | Does the first image create immediate reason to continue? |
| Narrative structure | 15 | Does the opening promise reach a payoff; do intermediate states change? |
| Concept-to-image fidelity | 10 | Does the actual image express the concept rather than merely look good? |
| Subject/asset consistency | 10 | Faces, buildings, objects, signage stable? |
| Temporal consistency | 10 | Flicker, texture jump, random background mutation? |
| Motion / camera | 10 | Movement intentional, smooth, plausible, editable? |
| Physical/spatial logic | 5 | Geometry, occlusion, gravity, screen direction coherent? |
| Visual system | 10 | Palette, archive treatment, camera grammar, typography coherent? |
| Audio / subtitle | 5 | Sound supports structure; text readable and accurate? |
| Evidence/rights/AI disclosure | 10 | Historical evidence and legal/ethical gates passed? |

For a judged historical film, score below 80 should normally trigger revision; factual/evidence failures are fatal regardless of score.

## 11. Controlled variants: test one question at a time

If the user can preview variants with classmates, mentors, judges, or a small blind viewer group, test one dominant variable per comparison:
- first-frame visual A vs B;
- opening VO line A vs B;
- rupture timing earlier vs later;
- ending payoff A vs B;
- sound-before-picture vs picture-before-sound transition.

Keep the rest constant. Do not compare two entirely different films and call it an A/B test.

For competition work without public traffic, use qualitative signals:
- which version creates the same intended interpretation across viewers?
- which version produces fewer clarification questions?
- which opening makes viewers predict the right central question?
- which ending is recalled 10 minutes later?

## 12. What to archive as reusable learning

After lock, save:
- winning opening/ending anchor pair
- rejected anchor variants and why
- motion-prompt variants
- generation model/version/reference map
- failed-shot modes
- approved fallback patterns
- viewer/judge feedback
- changes made after animatic

The durable asset is not one “magic prompt”; it is the decision history connecting concept -> evidence -> anchors -> motion -> edit -> review.
