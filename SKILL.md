---
name: historical-shortfilm-director
description: Plan and produce evidence-grounded historical short films, including source review, storyboards, reconstruction, code-rendered motion, continuity and local finishing. Keep critique, prompt-only and maintenance requests within their stated scope.
license: MIT
metadata:
  author: historical-shortfilm-director contributors
  version: "3.3.0"
---

# ChronicleFrame — Historical Shortfilm Director

An evidence-grounded Agent Skill and production runtime for historical short films.
Direct a concrete human-scale story while keeping sources, production state and the
delivered media auditable. An agent performs research and semantic review; the local
runtime preserves state, plans, receipts, hashes and deterministic finishing.

Runtime: Python 3.10+. Media operations need optional dependencies and FFmpeg;
external generation needs an available agent tool or operator. Local planning needs no account.

## Route by the requested outcome

- Maintenance or bounded critique: inspect the relevant files, complete that scope and
  its checks. Do not initialize a film or spend generation credits.
- Research, script, storyboard or prompt-only work: deliver the requested artifact.
  Read [historical evidence](references/HISTORICAL_EVIDENCE.md),
  [story design](references/STORY_DESIGN.md) or
  [script/storyboard](references/SCRIPT_STORYBOARD.md) as needed.
- Production or continuation: resume verified project state, preserve existing valid
  decisions and execute authorized work through the loop below.

## Evidence discipline

Keep archival evidence, supported inference, restoration, reconstruction and generated
media distinct. A restoration does not replace its original scan. Reconstructions need
clear disclosure, sources and limits. Generated media never becomes historical evidence.
Record claim IDs and allowed wording before writing consequential narration or images.
Preserve conflicting sources and unresolved claims rather than making the story convenient.

Use source/code overlays for evidence-critical text, faces, signage and document regions.
Hash the source and derivative separately. Existing generated work is reused only when
explicitly selected; do not delete original materials or approved baselines.

## Local preparation

Install the repository runtime in an isolated environment, then use `hsd --help`.
The normal profile is generic; institution-specific rules are optional data profiles.

```text
hsd init --title "Film title" --profile generic --dir "<new-project-dir>"
hsd validate "<project-dir>"
hsd prepare "<project-dir>"
hsd status "<project-dir>"
hsd next "<project-dir>"
```

Populate `03_production_graph.json` before `prepare`. The graph is the shared contract
for frames, motion units, joins and a timed preview. Read
[production graph](references/PRODUCTION_GRAPH.md) for the retained schema and
[execution protocol](references/EXECUTION_PROTOCOL.md) for exact receipt/review records.
Preparation compiles work; it never executes a generator or approves a gate.

## Execution and review

Use `claim → actual tool/operator action → receipt → ingest → review → accept`.
Read [provider capabilities](references/PROVIDER_MODEL.md) and use only the tools,
schemas, account access and capabilities actually available in the current environment.
This runtime provides no hidden direct generation API or browser implementation.
For an optional provider, read only its relevant workflow:
[Flow](references/providers/FLOW_AUTOMATION.md),
[image tools](references/providers/IMAGE25_AUTOMATION.md) or
[Claude Code video](references/providers/CLAUDE_CODE_VIDEO.md).

Claude Code makes video by writing programs, not by sampling a video model. Route
archival-photo motion, document details, titles, maps and graphic resets to `CODE` units:
write a scene from `hsd code brief`, check stills with `hsd code preview`, then
`hsd code render` and review its contact sheet like any candidate. A code render moves
verified pixels and exact text; it never synthesizes imagery or becomes evidence.

Technical decode, file hashes and endpoint metrics supplement semantic/historical review;
none alone proves that a candidate is acceptable. Bind reviews to actual candidate hashes.
Resolve failed dimensions with a targeted edit, changed route, bridge or different evidence
contract. Two distinct failures on the same dimension require rerouting; avoid blind rerolls.
Read [QC and retry](references/AUTO_QC_AND_RETRY.md) when a candidate fails.

## Human decisions

Use G1 for story, G2 for representative visuals, G3 only for exceptional motion/historical
risk and G4 for picture lock. Routine clerical preparation and ordinary passing assets do
not need repeated permission. Only an actual human decision can set `APPROVED`; record
the decision reference and reviewed artifact hashes. A plan's readiness label is separate.
Read [human gates](references/HUMAN_GATES.md). Preserve valid authorization; ask about
material changes in paid scope, creative mechanism or publishing destination.

## Preview, finishing and truthful completion

`hsd animatic` makes a still-based timed preview. Label it `PREVIEW_ONLY`; it does not
prove generated motion, semantic quality or human approval. Use it to review pacing,
source order and temporary audio. G2 should review a compact representative package.

For an assembled picture, preserve registered trims and preview the actual joins. After
actual G4 approval, finish credits, disclosures, subtitles and sound, then run full decode,
duration and file-integrity checks. Read [local finishing](references/LOCAL_FINISHING.md).

Distinguish `PLANNED_UNEXECUTED`, prepared queue, submitted request, downloaded candidate,
accepted asset, preview, assembled picture and delivered final. A produced film requires
playable verified media, current decisions, matching hashes, semantic/technical reviews
and every required unit. If access prevents execution, report the precise remaining step.

## Optional examples and maintenance checks

The [synthetic example](examples/minimal/README.md) runs with no paid generation.
The [JNU gate example](examples/jnu-gate/README.md) demonstrates an optional historical
profile; its claims and design constraints are example material, never framework defaults.

```text
hsd validate --skill .
python -m pytest
```

Media tests run separately. Offline tests do not establish live-provider quality.
See [contributing](CONTRIBUTING.md) for test layers and compatibility maintenance.
