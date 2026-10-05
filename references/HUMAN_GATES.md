# Human gates — 3.1

Three normal decisions and one conditional escalation. User authorization in the
current conversation is sufficient; never ask again just to fill a field.

| Gate | Concrete package the agent prepares first | Human judgment | Work that continues |
|---|---|---|---|
| G1_STORY | Distinct story mechanisms, recommendation and evidence risks | Choose the narrative mechanism | Inventory, factual verification, safe prototypes within requested scope |
| G2_VISUAL | Opening/ending, small hero/style board and timed visual animatic | Approve the visual system and rhythm | Candidate QC, prompts, independent source preparation |
| G3_HERO_MOTION | Winner/runner-up videos and exact unresolved issue | Only consequential motion/reconstruction choices | All independent routine jobs and their acceptance |
| G4_PICTURE_LOCK | Full picture master with temp sound and exception list | Approve sequence-level result | Technical export preparation |

After G2, faithful routine derivatives of approved hero states are AUTO, including
code-repeated P3 overlays whose source/geometry contract has not changed. Do not
reclassify every derivative as hero simply because it includes an approved face/name.
Escalate when the meaning, identity treatment, motif or source interpretation changes.

Plan-table `Approval` is an **agent readiness label**. Empty/PENDING plan rows may
compile; runtime enforces dependencies and actual gates. Explicit REVISE/REJECTED/
BLOCKED rows stay held. Do not confuse permission to create a candidate with approval
of the candidate. `REVIEW` is not a generation block.

Record actual decisions:

```text
python scripts/approve_gate.py "<project>" G2_VISUAL APPROVED --decision-ref "user message timestamp/id" --note "Approved visual family" --artifact "reviews/g2_visual_review.html" --artifact "assets/candidates/HERO/<candidate>.png"
```

Attach the actual selected media as artifacts, not only a screenshot or a board file.
For multiple winners repeat `--artifact`. The script stores hashes; later artifact
changes make the decision STALE. Use `REVISE` on the earliest affected gate to reset
downstream gate states, then regenerate only affected work. Existing unaffected source
and candidate histories remain available for inspection.

For no motion escalations:

```text
python scripts/approve_gate.py "<project>" G3_HERO_MOTION NOT_REQUIRED --note "Compiled motion queue contains no human escalation"
```

Only G3 can be skipped automatically, and the compiler's actual queue is checked.
Silence, elapsed time, script exit success or agent preference is never approval.
