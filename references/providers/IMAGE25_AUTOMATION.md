# GPT Image 2.5 visual-state factory — 3.1

Use image generation/editing as the art department, not merely to decorate a final
prompt pack. Generate concept studies, character/object/world masters, clean plates,
lighting variants, archival surrounds, depth-separated layers, opening/ending pairs,
seam surfaces and bridge frames that make ambitious Flow transitions reachable.

## Models and real tool controls

OpenAI documents `gpt-image-2.5-flare` for fast everyday image production and
`gpt-image-2.5-sunburst` for editing precision. Our production policy prefers Flare for
exploration/routine synthesis and Sunburst for hero states and demanding edits. This
is a workflow recommendation, not a measured benchmark. Sources and refresh rules:
`CAPABILITY_SOURCES.md`.

The native image tool may expose only prompt and references, without a model selector,
quality, size or seed parameter. In that case record requested model and actual model
as unexposed; do not add unsupported fields or claim the selected variant. Express
aspect/composition/transparent-background intent in the prompt and verify the output.
If exact model selection is mandatory but not available, report that limitation and
use an explicitly authorized supported path. Never silently replace GPT Image 2.5
with Flow's image model. Model documentation does not prove account access.

Use the native image tool by default. For edits inspect each local input first and
pass the exact files through the tool's current supported reference mechanism. For
new scenes with no input images omit edit references. One native call per distinct
state or requested candidate unless the actual tool explicitly supports batching.
Do not use a storyboard grid as multiple final frames: generate their masters separately.

## State design and reference hygiene

1. Assign a state ID, intended shot role, pixel locks, immutable geometry, permitted
   changes and acceptance criteria. Reference IDs resolve to hashed local masters.
2. Give each reference one role: edit target, identity, setting, composition, style or
   insert source. Avoid unrelated references. Keep the same subject/architecture master
   across a family. A generated reconstruction reference is never SOURCE_VERIFIED.
3. State purpose, concrete camera/composition, one requested change, KEEP constraints
   and post-only regions. For a subsequent edit describe the delta. Compare to the
   original master after every change; if drift accumulates, restart from that master.
4. Generate coherent alternatives, not superficial seed variations. Use a current
   accepted result for a bounded local edit when it is close; do not recreate the world.
5. Inspect all outputs. Rank contract/identity/composition/seam suitability ahead of
   beauty; reject historical contradictions independently of the numeric score.

## Exact regions and code

P0 free synthesis; P1 geometry/continuity; P2 archival evidence regions; P3 identity,
source words and factual signs. Use image synthesis aggressively around P2/P3 regions,
then restore them using `seal_evidence.py`. It creates a separate lossless PNG and
checks source pixels after composition. Never inpaint a historical face and call it
restored evidence. For changed perspective, keep the source on a controllable plane
or build a task-specific checked transform; do not treat a prompt as a pixel lock.

For the queue's HYBRID job, call the image tool, save the raw result, seal the evidence,
then ingest/review the sealed derivative. The generation receipt still identifies the
real raw provider result; overlay receipts link original and final. Generated alpha
is retained; do not flatten an intended transparent layer. Detailed commands are in
`EXECUTION_PROTOCOL.md` and `LOCAL_FINISHING.md`.

## Suggested creative uses

- Compose two motif-related hero states as siblings from one master, with different
  viewpoint/meaning; let Flow handle a local movement and use a cut for an era reset.
- Build clean foreground, archival plane and environment plates; code animates exact
  planes while Flow supplies atmosphere/action where deformation is tolerable.
- Use Image 2.5 to design a reachable midpoint; generate two shorter movements instead
  of forcing one impossible semantic morph.
- Explore light, material and frame rhythm before high-resolution final states. Preserve
  the approved composition when refining detail, rather than changing the story late.
