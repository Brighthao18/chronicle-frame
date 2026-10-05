# Claude Code video: code-rendered units

Claude Code generates video by writing a program, not by sampling a video model. A `CODE`
unit's program is a declarative scene (or, by explicit opt-in, a Python program) that the
local runtime renders deterministically with Pillow and FFmpeg. Any coding agent or a person
can author it; Claude Code is the intended author, interactively or through a headless
`claude -p` session. The runtime renders the program itself, so its receipt is an
observation of work it performed. Review and acceptance remain explicit decisions.

## When a CODE unit is the right route

Scene renders move, scale, rotate and fade verified inputs and draw exact text and boxes.
They never synthesize, retouch or recolour imagery, so archival pixels stay intact up to
resampling. That makes them the strongest route where generative video is weakest.

| Need | Treatment |
|---|---|
| Archival photograph as motion | Image layer with keyed `scale`, `ax`, `ay` (slow push, pan, settle) |
| Reveal a detail of a letter, map or document | Push toward the detail, then a `rect` outline or dimming panel |
| Titles, dates, place names, disclosures | `text` layer with a registered font and ledger-approved wording |
| Graphic or occlusion reset between scenes | Animated `rect` wipe or fade for a `GRAPHIC_RESET` join |
| Then-and-now or source comparison | Two image layers, crossfaded or side by side |
| Procedural map or chart (opt-in) | Python program that draws exact frames |

Use image or Flow routes for performances, invented architecture, crowds and anything that
needs new imagery. A code render is still a derivative: label reconstructions, keep source
credits and never present an enlarged detail as sharper evidence than its scan.

## Graph and job

A `CODE` unit needs the usual `action` and `camera` (the reviewer checks the motion against
them) and lists every asset the program may read, images and fonts alike, in `ingredients`.
`start` and `end` are endpoint contracts: acceptance compares the first and last frames with
them. `source_video` and a `FLOW_EXTEND` join into a `CODE` unit are rejected. Give a
`preview_frame` so the still animatic can show the unit.

```json
{
  "id": "U4",
  "mode": "CODE",
  "ingredients": ["SRC_LETTER", "FONT_SERIF"],
  "duration_s": 5,
  "edit_s": 4,
  "in_s": 0.5,
  "action": "Push slowly toward the signature, then outline it.",
  "camera": "One eased push-in; no rotation.",
  "preview_frame": "LETTER_STILL"
}
```

One film-wide `render` block sets the format of every `CODE` unit; it defaults to 1920x1080
at 25 fps, the default assembly format. Width and height are even integers.

```json
{"render": {"width": 1920, "height": 1080, "fps": 25}}
```

`hsd prepare` compiles each `CODE` unit into a video-queue job with provider `code`, mode
`CODE`, the render format and a code render contract instead of a Flow prompt. Its candidates
go to `generated/code_candidates/<unit>/` and its accepted clip to
`generated/code_approved/<unit>.mp4`, which the direct assembly manifest reads. Job IDs keep
the compatibility prefix `FLOW_`, which selects no vendor.

## One-time setup per authorized wave

```text
hsd code probe "<project>"
```

The probe observes FFmpeg (with libx264), Pillow and OpenCV and records the `code` capability
with `execution: "local-render"`, evidence and a timestamp. Like every observation it expires
after 24 hours. Code jobs also need the existing authorization reference, a positive
`code_output_limit` and the G2 decision, exactly as other motion work does.

```json
{
  "authorization": {
    "reference": "<the user's request that authorizes this production wave>",
    "code_output_limit": 12,
    "claude_code_session_limit": 6,
    "claude_code_max_budget_usd": 2.0,
    "claude_code_share_inputs": false
  },
  "code_render": {"python_programs": false, "timeout_s": 600}
}
```

Output limits are attempt ceilings, not prices. Local renders cost no provider credits, but
the same discipline keeps attempts countable and bounded.

## Interactive loop in Claude Code

```text
hsd next "<project>"
hsd code brief "<project>" FLOW_U4
hsd code preview "<project>" FLOW_U4 --program programs/U4.scene.json
hsd code render "<project>" FLOW_U4 --program programs/U4.scene.json --author "Claude Code session"
hsd runtime "<project>" review FLOW_U4 work/reviews/<token>.json
hsd runtime "<project>" accept FLOW_U4
```

1. `brief` prints the authoring brief and saves it to `work/code_briefs/<job>.md`: the
   compiled contract, the exact format (frame count and the time of the last frame), the
   edit range, endpoint duties, joins, verified inputs with provenance, the rules, earlier
   reviews of this job and the complete scene format. Write the scene where it suggests.
2. `preview` renders full-resolution stills (default: first, edit in, edit middle, edit out,
   last) and a contact sheet under `work/code_previews/`. It records nothing, needs no gate,
   and is the place to iterate. Read the contact sheet before rendering.
3. `render` renders every frame before claiming anything. A program that fails to parse,
   crashes, mismatches the format or fails the full decode costs no attempt and changes no
   runtime state; a failed render keeps its bundle and logs for diagnosis. A valid output
   is claimed, receipted and ingested through the normal
   runtime functions; an attempt claimed earlier with `hsd runtime ... claim` is fulfilled
   instead. The command prints the candidate, contact sheet, render receipt and a review
   template whose checks are all `UNCERTAIN`.
4. Review the actual contact sheet and candidate. Replace every check with a real judgment
   (all eight video checks apply) and add substantive notes; the unchanged template is
   rejected. A failed review with a classified `failure_code` re-queues the job; the next
   brief lists the failure. Two failures on the same dimension still require a reroute.
5. `accept` applies the video checks every provider shares: enough duration for the trim,
   endpoint similarity against `start`/`end`, the last-frame snap heuristic and any human
   gate covering the candidate hash.

## Scene format

`hsd code brief` embeds this reference, so an author needs nothing else.

A scene is one JSON object with `"schema": "hsd-scene/1"`, an optional opaque `background`
(`#RRGGBB`, default black), optional `notes` and a non-empty `layers` list drawn bottom to
top. Width, height, fps and duration come from the job, never from the scene. Coordinates
are fractions of the frame: x grows right, y grows down and (0, 0) is the top-left corner.
Frame i is shown at t = i / fps, so a 4 s clip at 25 fps ends at t = 3.96 s.

Every layer may set `id`, `notes`, `start_s` and `end_s` (visible while
start_s <= t < end_s) and `keys`: keyframes with strictly increasing `t` in seconds. A key
sets animatable properties and an optional `ease` (`linear` default, `in`, `out`, `in_out`,
`hold`) for the segment arriving at it. A property holds its first keyed value before its
first key and its last value after its last key. An animatable property may also be set on
the layer as a constant, used whenever no key sets it.

| Layer | Fields | Animates (defaults) |
|---|---|---|
| `image` | `asset` (an input ID), `fit`: `cover` default, `contain`, `width`, `height`, `none` | `x`, `y`, `ax`, `ay` (0.5), `scale` (1), `rotation` (0, degrees clockwise), `opacity` (1) |
| `text` | `text` (exact wording, newlines allowed), `size` (fraction of frame height, 0.05), `color` (#FFFFFF), `font` (an input ID), `align` (`left`, `center`, `right`), `line_spacing` (1.2) | as `image` |
| `rect` | `color` (#000000, `#RRGGBBAA` allowed), `outline` (stroke as a fraction of frame height; omit to fill) | `x`, `y` (0), `w`, `h` (1), `opacity` (1) |

An image or text layer places its own point (`ax`, `ay`), given as fractions of its width
and height, at frame point (`x`, `y`), then scales and rotates about it. `fit` sizes an image
to the frame at scale 1; text at scale 1 is `size` tall. Validation reports every problem
with its JSON path, for example `layers[1].keys[0].opacity: must be in 0..1`.

A push toward a signature that is outlined once the move settles, with a captioned source:

```json
{
  "schema": "hsd-scene/1",
  "background": "#0B0D10",
  "notes": "The signature ends centred; the outline appears only after the move settles.",
  "layers": [
    {"id": "letter", "type": "image", "asset": "SRC_LETTER", "fit": "contain", "keys": [
      {"t": 0, "scale": 1.0, "ax": 0.5, "ay": 0.5},
      {"t": 3.0, "scale": 2.2, "ax": 0.68, "ay": 0.82, "ease": "in_out"}]},
    {"id": "outline", "type": "rect", "color": "#E8C46A", "outline": 0.004,
     "x": 0.38, "y": 0.42, "w": 0.24, "h": 0.16, "keys": [
      {"t": 3.0, "opacity": 0}, {"t": 3.5, "opacity": 1, "ease": "out"}]},
    {"id": "credit", "type": "text", "text": "Archive letter, detail", "font": "FONT_SERIF",
     "size": 0.04, "ax": 0, "x": 0.06, "y": 0.9, "keys": [
      {"t": 0.5, "opacity": 0}, {"t": 1.2, "opacity": 1, "ease": "out"}]}
  ]
}
```

A graphic reset: a dark panel wipes across the gate to leave a clean surface for the cut.

```json
{
  "schema": "hsd-scene/1",
  "layers": [
    {"id": "gate", "type": "image", "asset": "SRC_GATE", "scale": 1.04},
    {"id": "wipe", "type": "rect", "color": "#0B0D10", "y": 0, "h": 1, "keys": [
      {"t": 0, "x": 1.0, "w": 0.0},
      {"t": 1.2, "x": 0.0, "w": 1.0, "ease": "in_out"}]}
  ]
}
```

Authoring checks that catch most failed reviews: key every animated property on the first
key; keep cover-fit images covering the frame for the whole clip (the renderer warns with the
first exposed frame); keep the decisive action inside the edit range; avoid motion in the
first and last 0.2 s when a join needs a stable seam; ease camera moves; and do not enlarge a
detail so far that the source resolution, not the story, becomes the subject.

Register a font file (`.ttf` or `.otf`) as an input for reproducible typography and for any
script the default font lacks, such as Chinese. Without `font`, Pillow's bundled scalable
font is used and its version is recorded. Complex shaping (Arabic, Indic scripts) depends on
the local Pillow build.

## Python programs (opt-in)

Some shots need procedural drawing: an animated route on a map, a chart, a generated
texture. Set `code_render.python_programs` to `true` only after reviewing the program. It is
executed with this runtime's interpreter in isolated mode (`-I`), in a scratch directory,
with a minimal environment that carries no inherited credentials, and with `timeout_s`.
This is not a sandbox: the program runs with the user's file-system permissions, so render
only programs you would run yourself and never ones from an untrusted project.

The program receives one argument, a JSON context file with `width`, `height`, `fps`,
`duration_s`, `frame_count`, `frame_indices`, `frames_dir`, `inputs` (`{ID: {path, sha256}}`)
and `seed`. It must write exactly `frames_dir/{index:06d}.png` for every requested index, each
of the job's size, and nothing else there. Previews request only a few indices; renders
request all. The runtime encodes the frames itself, so the format is always the job's.

```python
import json, os, sys
from PIL import Image, ImageDraw

context = json.load(open(sys.argv[1], encoding="utf-8"))
base = Image.open(context["inputs"]["SRC_MAP"]["path"]).convert("RGB")
base = base.resize((context["width"], context["height"]))
for index in context["frame_indices"]:
    frame = base.copy()
    progress = index / (context["frame_count"] - 1)
    ImageDraw.Draw(frame).line((100, 500, 100 + 800 * progress, 300), fill=(200, 40, 40), width=6)
    frame.save(os.path.join(context["frames_dir"], f"{index:06d}.png"), compress_level=1)
```

Headless sessions never write Python programs; only scenes.

## Provenance

Each render keeps a bundle in `work/code_renders/<render_id>/`: the exact program bytes that
ran, `render.json`, the FFmpeg log, the contact sheet and, for Python, `program.log` and its
context. `render.json` records the program hash and source path, the declared or headless
author, the verified inputs with hashes, the runtime input hash, the format, the output hash,
the toolchain (runtime, Python, Pillow, FreeType and FFmpeg versions), the portable encoder
arguments, font provenance and renderer warnings. No absolute paths are recorded. The runtime
receipt adds `handle: "local-render:<render_id>"`, `actual_mode: "CODE"` and the hashes of
`render.json`, the program and the output, and the accepted asset keeps that receipt.

Encoding is H.264 (`yuv420p`, CRF 18, BT.709 tags) piped from raw RGB frames with argument
vectors only. With the same program, inputs and toolchain a re-render is byte-identical; a
different FFmpeg, Pillow or FreeType version may legitimately change the bytes.

## Headless Claude Code authoring

`hsd code author` runs one `claude -p` session that writes a scene for one job, for when the
pipeline is driven from a terminal, a script or another agent. Inside an interactive Claude
Code session it refuses to nest a second session; author the scene directly from the brief.

```text
hsd code probe "<project>" --claude
hsd code author "<project>" FLOW_U4 --render
```

The probe runs `claude --version` and `claude --help` and records the version and the flags
this adapter relies on. `--print`, `--output-format`, `--permission-mode` and `--tools` are
required; `--restricted`, `--permission-prompts`, `--max-budget-usd` and `--model` are used
when listed. The executable comes from `HSD_CLAUDE` or `PATH`, never from project files, and
its version must still match the observation when a session starts.

Each session is reserved in the execution state before it starts and counts against
`claude_code_session_limit` even if it fails or times out. It runs in
`work/code_authoring/<token>/` with `BRIEF.md`, file tools only (`--tools Read,Write,Edit`,
`--permission-mode acceptEdits`), no shell or network tools, and the prompt to write
`scene.json` there. The record keeps the arguments (without the executable path), the session
ID, turns, reported cost, exit status, brief and scene hashes, scene validation problems and
any files the session created besides `scene.json`. `claude_code_max_budget_usd` caps each
session through `--max-budget-usd` and is refused if the CLI does not list that flag.

Data boundary: the brief (contract, input IDs, sizes, registry provenance notes and earlier
review notes) is always sent to the model. Input images are copied into the session only when
`claude_code_share_inputs` is `true`; confirm rights and the provider's data terms first.

Sessions may consume paid usage. This repository's tests use an offline stand-in for the CLI;
no live Claude Code session was run or is claimed as tested.

## Limitations

- Layers are images, text and rectangles; there are no video layers, masks, blurs, motion
  blur, depth parallax or audio. Sound belongs to the existing finishing stage.
- One render format per film; assembly scales and pads anything else.
- Text uses Pillow's FreeType layout. Register fonts for reproducible, script-complete text.
- Renders are deterministic per toolchain, not across different library versions.
- Technical checks and contact sheets support review; they cannot judge historical meaning.
