# QC and adaptive repair — 3.1

Every accepted candidate needs both real-file technical checks and recorded agent
visual/historical judgment tied to its SHA-256 and current input contract. The agent
performs that judgment; no user confirmation is needed for an ordinary AUTO result.

## Technical pre-screen

`media_check` decodes images or full-decodes video/audio with FFmpeg, records dimensions,
fps and duration. `auto_qc_media.py` adds first/last reference pHash and a tail-jump
heuristic for ranking. These are screening metrics, not proof of identity, action,
factual accuracy or seamless cuts. WARN requires inspection/repair or a justified
contract revision; do not silently lower a threshold merely to pass.

`extract_review_frames.py` creates timestamped review evidence. Inspect the full clip
when available; otherwise inspect enough chronological samples and dense regions
around abrupt motion, faces/text and both actual trim boundaries. Record the reviewed
range and uncertainty; sparse frames do not prove absence of brief artifacts.

## Agent review record

Use the `review` JSON in EXECUTION_PROTOCOL. Checks include contract, identity/geometry,
text/evidence, composition, continuity, historical accuracy; video also needs
motion/camera and join checks. PASS means every required dimension passed. For fields
not relevant to the shot, record PASS with an explicit not-applicable reason in notes.
UNCERTAIN is not a pass. Score ranks only candidates without hard failures.

For EXACT_SEAM, compare outgoing `use_out - one frame` to incoming `use_in`, not merely
the first and final frames of their longer generated clips. Include screen direction,
speed, illumination and geometry; a common source seam image does not guarantee an
actual encoded join. For other cuts judge the intended match/reset. Use a short
two-clip preview or assembled sequence before picture lock.

## Repair instead of blind rerolls

Classify failure: CONTENT_DRIFT, IDENTITY_GEOMETRY_DRIFT, TEXT_EVIDENCE_DRIFT,
MOTION_PATH_FAIL, CAMERA_FAIL, ENDPOINT_SNAP, SEAM_FAIL, LOCAL_ARTIFACT, AUDIO_FAIL,
TECHNICAL_FAIL, PROVIDER_FAILED. After two distinct candidates fail in one dimension,
the runtime requires rerouting. A repeated review of the same file is not another failure.

Pick the correction that preserves the approved creative mechanism: source-overlay
repair, delta image edit, local video edit, simplified action, bridge/split/reset,
re-anchoring from the master, then fresh generation. Change plan + prompt before sync;
prior attempts remain in history and continue to count toward the provider output cap.
An ambiguous provider timeout stays ACTIVE until its actual operation is reconciled.

`--promote-auto` no longer copies a high-scoring clip blindly. It delegates to runtime
acceptance, which requires matching semantic review, source-lock proof where required,
fresh inputs, enough duration and relevant human decisions. It cannot promote raw
files simply found in a candidate folder.
