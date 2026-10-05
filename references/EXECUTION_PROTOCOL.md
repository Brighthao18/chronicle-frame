# Agent execution protocol — 3.1

The scripts run locally. The agent is responsible for actual image calls, observed
browser actions, factual judgment and truthful records. File values below are schema
examples, never evidence of access, a user approval or completed generation.

## Capability and authorization setup

`init_project` creates empty capability/policy templates. Fill them from actual current
tools/UI and the user's existing generation request. Do this once per authorized wave,
not before each shot. Do not populate them during a Skill-only editing task.

`00_capability_snapshot.json` supports these execution fields in addition to local probes:

```json
{
  "image": {
    "available": true,
    "observed_at": "<ISO-8601 UTC observation>",
    "evidence": "<actual tool schema/observation reference>",
    "model_selectable": false,
    "models": []
  },
  "flow": {
    "available": true,
    "observed_at": "<ISO-8601 UTC observation>",
    "evidence": "<observed authenticated project/model menu>",
    "execution": "browser",
    "modes": {
      "FRAMES": {"model":"<actual selected model>","durations_s":[4,6,8],"max_references":2}
    }
  },
  "local": {"ffmpeg_path":"<existing executable if not on PATH>"}
}
```

Modes, limits and duration lists must reflect the live surface, including Ingredients,
Extend and Omni edit independently. Omit max_references if not verified; inspect it
before upload instead of guessing. Native image tools without model selection use
`model_selectable:false`; the packet records preference separately from actual model.

`00_execution_policy.json`:

```json
{
  "schema_version":"3.1",
  "sampling":"adaptive-until-pass",
  "authorization":{
    "reference":"<existing user request identifying the permitted production wave>",
    "image_output_limit":24,
    "flow_output_limit":12
  }
}
```

The numbers are illustrative output ceilings, not defaults or prices. Choose a bounded
wave within already authorized scope; if the user supplied a budget preserve it and
also track actual currency/credits from provider receipts. Do not reset spent attempts
by recompiling or increasing limits without a corresponding scope decision. Reserved,
failed and ambiguous attempts conservatively count until the next authorized wave.

## Plans and graph

Populate the initialized frame/endpoint/blueprint tables. Compile then sync:

```text
python scripts/compile_image25_jobs.py "<project>"
python scripts/compile_flow_prompts.py "<project>"
python scripts/compile_flow_jobs.py "<project>"
python scripts/production_runtime.py "<project>" sync
python scripts/production_runtime.py "<project>" next
```

Only compile a stage when its real inputs are ready. Empty tables are not completed
work. Explicitly blocked plans stay blocked. The frame plan can add `Model preference`;
the endpoint plan can add `Ingredient IDs` and `Source video ID`. Register these IDs
before dispatch. FLOW_EXTEND joins supply predecessor job dependencies; explicit source
clips may also be registered. Use distinct IDs for raw sources and produced frames.

Prompt linter findings are editorial warnings by default; inspect them automatically
and revise real problems. `--strict` is available for an explicitly strict review.
Compilation/schema/endpoint errors remain blocking. Do not expand a precise motion
prompt merely to satisfy a historical word-count heuristic.

Every generated reference producer must be ACCEPTED before a downstream job runs.
`sync` rejects dependency cycles, preserves unchanged work, and invalidates results
whose source or dependency hashes changed. Active operations keep their original
handles; reconcile them before replacing their specification.

## One image/Flow output

```text
python scripts/production_runtime.py "<project>" claim IMG25_FRAME_A
```

This persists an output reservation and writes `work/dispatch/<token>.json`. It contains
the contract, prompt, verified reference paths/hashes, actual supported selection and
dependency clips. It does **not** generate anything.

Now call the native image tool or operate Flow with this packet. Inspect local images
before editing, then use exactly the reference mechanism supported by the tool. For
Flow observe controls, upload the correct assets, select the recorded mode/model and
request one output. For a bounded native Agent batch first claim each independent job.

After actual submission/completion, write `work/receipts/<token>.json`:

```json
{
  "handle":"<actual tool call or Flow asset/task identifier>",
  "evidence":"<tool result or observed UI reference>",
  "actual_model":null,
  "actual_mode":"FRAMES",
  "provider_result_path":"<actual raw result when available>"
}
```

`actual_model` may be null only if model identity is not exposed. If a model was selected
it must match the actual receipt. Flow requires actual_mode. Record result paths and
provider usage when returned; never include credentials/session cookies.

```text
python scripts/production_runtime.py "<project>" receipt IMG25_FRAME_A <token> "work/receipts/<token>.json"
python scripts/production_runtime.py "<project>" ingest IMG25_FRAME_A <token> "<real-output-file>"
```

`ingest` copies a real validated output to a collision-safe candidate path. For exact
overlays run `seal_evidence.py` before ingest and ingest the sealed PNG. Keep its raw
generation receipt and overlay receipt. File extension must match the intended final
format; create and review a correctly converted derivative if the provider returns a
different format. Never rename JPG bytes to .png.

## Visual review and automatic selection

Inspect the actual candidate and relevant original references. For video inspect motion
and cut-boundary evidence; see AUTO_QC_AND_RETRY. Write `work/reviews/<token>.json`:

```json
{
  "sha256":"<ingested candidate SHA-256>",
  "reviewer":"<agent/model or human reviewer identifier>",
  "evidence":["<actual viewed files/frames/time ranges>"],
  "checks":{
    "contract":"PASS",
    "identity_geometry":"PASS",
    "text_evidence":"PASS",
    "composition":"PASS",
    "continuity":"PASS",
    "historical":"PASS",
    "motion_camera":"PASS",
    "join":"PASS"
  },
  "score":91,
  "notes":"<specific observed reasons; explain not-applicable dimensions>",
  "failure_code":null
}
```

The first six checks are required for images; all eight for video. This JSON stores
the agent's actual review, not a computed model-vision verdict. On failure use FAIL or
UNCERTAIN plus a classified failure_code; do not copy the passing example mechanically.

```text
python scripts/production_runtime.py "<project>" review IMG25_FRAME_A "work/reviews/<token>.json"
python scripts/production_runtime.py "<project>" accept IMG25_FRAME_A
```

AUTO candidates pass straight through when requirements hold. REVIEW candidates wait
only for their human gate covering the exact candidate hash. Build the compact board:

```text
python scripts/build_review_packet.py "<project>" --gate G2_VISUAL
```

After the user's real decision record the selected candidate files as gate artifacts
with `approve_gate.py`, then accept. Routine derivatives do not repeat that gate.

## Retry, interruption and reconciliation

Failed semantic reviews queue another output until the job cap or same-dimension limit.
After two failures change the route/contract, recompile and sync. Global spent-output
count includes old revisions. No re-review of an unchanged file creates a new attempt.

If a tool/UI call is uncertain, inspect its original handle. Do not call claim again.
For a known terminal provider failure or confirmed never-submitted claim, record:

```json
{"outcome":"FAILED","evidence":"<actual terminal provider observation>"}
```

```text
python scripts/production_runtime.py "<project>" reconcile FLOW_U1 <token> "work/receipts/reconciliation.json"
```

Allowed outcomes are FAILED, NOT_SUBMITTED, OBSOLETE. NOT_SUBMITTED is invalid after a
submission receipt. OBSOLETE means a retrieved/terminal result whose original inputs
have been superseded; keep it in provider/history and do not accept it. Timeouts are
not terminal observations. Never remove a runtime writer lock solely because it is old;
check the recorded PID and current process before recovering a crashed local writer.

If a human operates Flow because browser tools are unavailable, record Flow capability
as `execution:"operator"` using the observed/reported actual settings, not as automated
browser access. Reserve the specific job, supply its operator card, then record the
real returned asset/receipt and ingest it through the same review path.

## Code-rendered units

Provider `code` jobs (graph `mode: "CODE"`) skip the external handoff. The runtime is the
renderer, so it writes the receipt from what it observed:

```text
hsd code probe "<project>"
hsd code brief "<project>" FLOW_U4
hsd code preview "<project>" FLOW_U4 --program programs/U4.scene.json
hsd code render "<project>" FLOW_U4 --program programs/U4.scene.json
```

`render` renders and verifies the whole clip before it claims, so a broken program costs no
attempt. A valid output is claimed (or fulfils an attempt claimed earlier), receipted as
`local-render:<render_id>` with `actual_mode: "CODE"` and ingested. Review it with all eight
video checks and accept it as above. Never write a receipt for a code job by hand. Details:
[Claude Code video](providers/CLAUDE_CODE_VIDEO.md).
