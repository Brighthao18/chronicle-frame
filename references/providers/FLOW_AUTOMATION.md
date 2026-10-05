# Flow execution and repair — 3.1

Use authenticated browser/computer-use tools when present. Read their current tool
instructions. Discover the actual project, model menu, modes, reference inputs,
durations and download path from observed UI. There is no bundled Flow API client or
hardcoded selector robot; do not invent private endpoints or infer hidden DOM state.

## Native modes by purpose

| Need | Preferred route | Verify before dispatch |
|---|---|---|
| Reachable controlled start/end | FRAMES | Both endpoints, aspect, supported duration |
| Controlled entry, freer exit | START_FRAME | Start frame and exit contract |
| Continue the same action | EXTEND | Source clip eligibility, model, inherited tail |
| Repeated entities with flexible layout | INGREDIENTS | Named image/video refs and their roles |
| Repair an otherwise good clip | OMNI_EDIT | Actual edit feature, source clip and segment |
| No exact anchor required | T2V | Same source/evidence and motion review |
| Exact graphic/source-plane movement | `CODE` unit ([Claude Code video](CLAUDE_CODE_VIDEO.md)) | Deterministic motion and typography |

This is a purpose-based choice, not a mandatory order that always forces Frames.
Scene/era/identity resets use a designed cut, occlusion, graphic transition or bridge.
Image 2.5 can make these transitions visually rich without turning them into morphs.

## Agent-assisted batches

Flow's native Agent can generate variations, edit selected media, and work with
project context. Prefer it when it reduces repetitive UI steps **and** keeps the
specified model, refs, count and scene contracts verifiable. Supply concise project
instructions: source/reconstruction distinction, fixed identity, motion language,
no unrequested deletions or substitutions. Ask for bounded independent outputs,
with explicit job IDs and counts; reconcile every output to its requested job.

The bundled runtime reserves one output per claim. For a native Agent batch, claim
each independent job first and submit no more outputs than reserved. Record the same
observed batch handle plus per-output asset identity on each receipt. Do not put two
dependent units in a batch before the predecessor is accepted. If mapping is ambiguous,
use the standard prompt box for those units. Follow-up edits have their own claims.

## Browser operation loop

1. Check login/access once and record verified capabilities with observation time and
   evidence. Keep non-local observations when running local dependency detection.
2. Use `production_runtime next/claim`; gather only the packet's accepted references.
   Upload/reuse them by asset ID/hash. Explicitly assign ingredients and source clip.
3. Choose the live-supported model and shortest duration covering required usable
   footage plus handles. Never assume every mode shares the same duration options.
   If Frames is unavailable, revise the route deliberately; don't silently discard
   the end image. Record the revised contract before another claim.
4. Generate the reserved output. Observe its task/asset handle immediately and record
   receipt with actual model/mode. Reuse a live handle for status checks; a timeout is
   not failure. Do other ready work during generation when tools allow it.
5. Download from the observed result, verify playable media, ingest, extract start,
   intermediate, tail and intended cut frames. Inspect full action and boundary motion;
   isolated thumbnail similarity is not sufficient.
6. Register passing ordinary results automatically. Present only unresolved hero
   decisions at G3. Use Scenebuilder for useful sequence preview; local manifests and
   downloaded files remain the reproducible assembly authority.

## Repair strategy

Keep close winners. Use a targeted Omni edit for a local artifact/lighting defect when
available, preserving the original and checking the whole clip for new drift. Verify
edit-segment limits separately from upload limits. Use an extracted accepted stable
frame for continuation; do not call a planned end image an extracted frame.

Two failures on the same dimension trigger a changed motion path, bridge, ref set,
model-supported route or deterministic source-plane treatment. A changed contract
creates a new queue revision and invalidates dependent results. Escalate only if the
fix changes the approved narrative/visual meaning.

## Capability fallback

If tools cannot operate Flow, compile `compile_flow_operator_pack.py` and provide
ready references + copyable prompt + exact settings + download destination. User-only
login/challenge actions are legitimate handoffs; all decisions and local preparation
are completed first. Report `PLANNED_UNEXECUTED` until actual files are retrieved.
