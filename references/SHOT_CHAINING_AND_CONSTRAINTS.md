# Shot Chaining Under Tight Model Constraints

Use this reference when the production model has practical limits such as **max 3 reference images per shot** and **max 10 seconds per generated clip**.

## Core position

Using the **generated tail frame of shot N as the starting anchor of shot N+1** is often a better way to preserve continuity and organize sequences — **but only when the previous shot is already approved or at least directionally correct**.

Treat it as a controlled continuity strategy, not a blind rule.

## When shot chaining is better

Prefer chaining when at least one of these is true:
- the same gate / person / object / space must persist across adjacent shots;
- the next shot is a continuation, reveal, or reframing of the previous visual state;
- the edit depends on a match cut, carry-through movement, or camera-path continuity;
- the model tends to drift identity/geometry if every shot restarts from scratch.

## When *not* to chain blindly

Do **not** automatically extract the last frame and pass it forward when:
- the previous shot contains drift, text corruption, geometry damage, or unwanted hallucinations;
- the next shot should reset to a more authoritative archival or keyframe reference;
- the new shot needs a substantially different composition that the carried frame would constrain too heavily;
- a transition is conceptual/editorial rather than physical continuation.

In those cases, use a **manually approved end frame**, a repaired still, or a separate anchor frame instead of the raw generated tail frame.

## The default micro-shot rule

If a model can generate at most **10 s** per clip, do **not** design story beats around 10-second AI shots by default.

Use these defaults:
- **2–4 s**: high-control, continuity-sensitive action or transition shot
- **4–6 s**: normal narrative AI shot
- **6–8 s**: contemplative move, atmosphere, or slower reveal
- **8–10 s**: only when the dramatic value is clear and the model can hold continuity

Longer developments should be built as a **chain of linked micro-shots**.

## 3-reference budgeting rule

When only **3 reference images** are allowed, reserve them deliberately.

### Default priority

1. **Carry-forward continuity frame**  
   The approved last frame (or repaired near-last frame) from the previous shot.
2. **Stable identity / geometry frame**  
   The strongest authoritative image for the recurring gate, character, object, or composition family.
3. **New shot-specific control frame**  
   A composition target, end frame, route/map crop, document detail, or style reference needed only for this shot.

### If a shot does not need carry-forward continuity

Reallocate slot 1 to another high-value reference, for example:
- a second geometry reference,
- a close crop of historically exact text,
- a lighting/composition reference.

## Composite-then-generate strategy

If one shot needs more than 3 source materials conceptually, do **not** try to show the model all of them directly.

Instead:
1. decide the shot's **primary frame logic**;
2. prepare a **single composite anchor frame** or approved previsual still that already combines the necessary documents/photos/graphics;
3. use the composite as one reference, plus 1–2 additional continuity/geometry references.

This is especially useful for archive-heavy sequences, map-document composites, and motif shots in historical threshold films.

## Recommended chained-shot schema

Create or update `05c_shot_chaining_plan.md`. In v1.6, distinguish two different decisions: **whether the shot inherits the previous carry frame**, and **whether this shot should export a carry frame to the next shot**. A reset shot can therefore inherit `no` but export `yes`. Use the full slot-level table in the v1.6 section below.

Chain role examples:
- `CHAIN_START`
- `CHAIN_CONTINUE`
- `CHAIN_REVEAL`
- `CHAIN_BREAK`
- `CHAIN_RESET`
- `CHAIN_END`

## Tail-frame extraction rules

When using shot chaining, do not simply say “use the last frame.” Define **which frame** and **why**.

Recommended rule:
- inspect the final second of the approved shot;
- choose the frame with the cleanest geometry / least motion blur / strongest continuity value;
- if needed, use a near-final frame instead of the literal last frame;
- give the extracted frame a stable ID, e.g. `CF_S03_v2` (carry frame, shot 03, version 2).

## Prompt architecture for chained I2V shots

For continuity-sensitive image-to-video shots, the prompt should mostly describe **motion**, not static image facts already fixed by the references.

Suggested structure:

```text
SHOT ID:
CHAIN ROLE:
PREV SHOT:
START ANCHOR:
END TARGET:
REFERENCE BUDGET:
1) continuity carry frame
2) stable geometry/identity frame
3) shot-specific control frame

SUBJECT MOTION:
ENVIRONMENTAL / LAYER MOTION:
CAMERA MOTION:
TIMING:
END STATE:
CONTINUITY LOCKS:
NEGATIVE CONSTRAINTS:
EXTRACTION RULE FOR NEXT SHOT:
```

## Editorial logic

Chaining works best when the **edit itself** is planned.

Before generation, specify whether the next shot relates to the previous one by:
- continuation,
- reframing,
- reveal,
- match cut,
- axis continuation,
- border-line carry,
- sound bridge,
- rupture/reset.

If the editorial relationship is unclear, chaining will not rescue the sequence.

See the optional [historical profile applications](../examples/jnu-gate/references/FRAMEWORK_APPLICATION_NOTES.md) for institution-specific design.

## v1.6 — Automatic chain-prompt compilation

After `05c_shot_chaining_plan.md` is populated, run:

```bash
python scripts/compile_chain_prompts.py <project_dir>
```

The compiler produces:

- `06b_chain_prompt_pack.md` — one copy-ready English I2V prompt block per shot;
- `06c_chain_generation_runbook.md` — the sequential operator workflow for generating, reviewing, extracting a carry frame, and assigning/resetting the next shot.

### Slot-level planning is mandatory

Do not write one generic “reference budget” cell. Plan all three slots explicitly:

- `Ref1` — normally the carried continuity frame from the prior approved shot;
- `Ref2` — the authoritative recurring identity / geometry reference;
- `Ref3` — the shot-specific composition, end-frame, document crop, map crop, or approved composite reference.

If the shot is a reset, `Ref1` may be reassigned deliberately. The plan must say why.

### Recommended v1.6 table

| Shot | Duration | Chain role | Prev shot / source | Start anchor | End anchor target | Ref1 | Ref2 | Ref3 | Inherit prev carry? | Export carry to next? | Extraction rule | Reset conditions | Subject motion | Environment / layer motion | Camera motion | Timing | End state | Continuity locks | Negative constraints |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

### Compilation does not replace review

The compiler is deterministic bookkeeping, not an image-quality judge. The operator/agent must still inspect the previous shot before materializing the next carry frame.

Use this branch:

```text
previous shot approved?
├─ YES → inspect final second → choose clean tail/near-tail frame → save CF_<SHOT>_vN → put into next shot Ref1
└─ NO  → do not propagate → repair/regenerate previous shot OR activate next shot reset anchor
```

The literal final frame is not sacred. Prefer the cleanest near-tail frame when the last frame has motion blur, deformation, or transition contamination.
