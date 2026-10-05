> Optional historical example material. Source IDs and earlier creative decisions are illustrative.
> Recheck historical claims independently; this file grants no production authorization.
> No private source media, live-provider validation or current competition logistics are bundled.

# 《门外，是四海》 v2 Production Baseline

This file is a **project-state snapshot and migration guide**, not a substitute for the current project directory. If the live project contains a newer approved animatic, storyboard, evidence ledger, or prompt pack, the live project wins.

## 1. Latest known approved baseline

As of the 2026-09-10 project state:

- title: 《门外，是四海》;
- competition context: Jinan University 120th anniversary historical short film;
- orientation: 16:9 landscape;
- production mode: archival / AI / deterministic composite, with no live-action dependency;
- Animatic V1 approved;
- structure: `O1 / F1`, sequences `S00–S09`, and a **35-shot timeline**;
- the model-neutral prompt pack originally assumed each AI source clip would be 10 seconds, with only a registered sub-interval used in the final edit;
- the same pack assumed at most three uploaded image references per shot;
- historical faces, gate geometry, Chinese characters, documents, and photograph borders were treated as sealed pixels;
- dates, place names, numbers, subtitles, route nodes, title, source credits, restoration notes, and AI disclosure were kept out of the video model and added in post;
- shots marked `AI_OPTIONAL_POST_PRIMARY` already acknowledged that a deterministic composite could be more reliable than video generation.

These constraints are a strong starting point, but the 10-second-source and universal 3-reference assumptions were **pre-Flow/model-neutral planning assumptions**, not permanent artistic rules.

## 2. v2 migration objective

Do not throw away the approved 35-shot structure. Convert it from:

```text
approved animatic
→ 10-second model-neutral prompts
→ generate long source clips
→ find usable intervals
→ manually discover joins
```

into:

```text
approved animatic / 35-shot timeline
→ approved still assets for every critical visual state
→ planned seam/junction frames
→ Flow-native shot duration/mode
→ one motion contract per shot
→ predeclared usable interval
→ direct assembly from join contracts
```

The goal is to preserve the story decisions while reducing generation waste and edit labor.

## 3. Preserve the strongest existing project decisions

### Opening / ending anchors

Keep the approved `ANCHOR-O1` and `ANCHOR-F1` logic unless the user explicitly reopens the creative direction.

The late-film action where the archival card finally exits the present gate remains a strong payoff mechanism because it completes an action withheld at the beginning.

### Sealed evidence

These remain non-negotiable:
- no face animation inside archival photographs;
- no rewritten Chinese characters;
- no elastic gate geometry;
- no invented people or objects;
- no outpainting that falsely implies missing historical content;
- no AI-generated dates/place names/credits inside Flow footage.

### Historical photo behavior

For early Nanjing groups and Jianyang evidence, do not revert to isolated Ken Burns shots. Prefer:
- deterministic archive-space layouts;
- paper-card interactions;
- evidence constellations;
- geometry/white-border transitions;
- camera movement through a prebuilt composite.

The people inside the photographs remain still.

## 4. Replace the universal 10-second assumption

For Google Flow production, use the selected model/mode's actual supported duration choices.

Default migration rule:

```text
final edit shot length
→ add only the handle actually needed
→ choose the smallest supported Flow duration that covers it
```

Examples:
- 3-second edit shot → usually 4-second source, not 10;
- 5-second edit shot → usually 6-second source;
- 7-second edit shot → usually 8-second source;
- true 9–10 second shot → use a mode that actually supports it or split it intentionally.

Do not hard-code 4/6/8/10 forever; verify the current Flow UI/model at execution time.

## 5. Replace reference-count thinking with role thinking

The old 3-reference upload order remains useful as a legacy fallback, but Flow should be planned by role:

- Ingredients / Characters for recurring identity or appearance;
- Start Frame for exact shot entry;
- End Frame when a precise reachable endpoint helps;
- planned Seam Frame when two shots should join cleanly;
- deterministic composite for multi-source evidence layouts;
- post-only track for text/map labels/credits.

The project should not force every conceptual source into the video model's reference slots.

## 6. ChatGPT Image 2.5 role in this project

Use Codex/Zcode or another capable agent to call ChatGPT Image 2.5 for controlled still construction when useful.

Priority tasks:
- create or edit clean non-evidentiary backgrounds;
- construct metaphorical threshold spaces;
- harmonize lighting outside sealed archival content;
- create start/end/seam/bridge visual states;
- create clean composite bases that will later receive original archival pixels.

For archival people, signage, documents, and exact gate text:

> generate/edit the surrounding world if needed, then re-overlay the original pixels deterministically.

## 7. Seam strategy for this film

Prefer a small set of recurring join mechanisms so the film feels designed rather than patched together:

1. **threshold seam** — shared door/gate opening or dark interior;
2. **paper-edge seam** — photo border or document edge becomes the next frame boundary;
3. **axis match** — gate centerline/arch geometry matches across time;
4. **route-line seam** — architectural edge becomes a map/route line;
5. **black/silence reset** — reserved for rupture/interruption;
6. **evidence-card seam** — one rigid archival card exits/reveals the next state;
7. **Flow Extend** — only when motion and world genuinely continue.

Do not invent a different transition gimmick for every shot.

## 8. Direct-assembly target

For each `SH001…SH035`:
- fixed story role;
- fixed final edit duration;
- Flow mode;
- approved Start Frame;
- optional approved End/Seam Frame;
- planned usable interval;
- join-out contract to the next shot;
- deterministic fallback.

The finished generation package should allow an agent to build a cut-order manifest without making new creative decisions.

## 9. Current project-specific review rule

A generated clip is not approved just because its middle looks good. It must pass:
- first 10% boundary;
- last 10% boundary;
- sealed-pixel/geometry review;
- endpoint adherence;
- seam compatibility with the next shot;
- usable-interval timing;
- direct-assembly test.

If a clip cannot pass the seam test after two targeted attempts, use the registered deterministic fallback instead of defending the AI route.
