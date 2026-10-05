# Local media automation — 3.1

Prefer project-local dependencies. `check_dependencies.py` reports installed modules;
FFmpeg resolution checks `00_capability_snapshot.json` → `local.ffmpeg_path`, then
`HSD_FFMPEG`, system PATH, then an installed imageio-ffmpeg binary. Do not alter global
PATH to make a render work. Install required dependencies only after checking existing
ones, and report any installation. No ffprobe is needed by the new full-decode checker.

## Exact source regions

Fill `03e_evidence_overlay_plan.csv` with approved/READY rows:

```text
frame_id,target_path,source_path,source_box,target_xy,alpha_mask_path,reason,approval,output_path
HERO,assets/raw/hero.png,materials/photo.png,FULL,"120,80",,sealed archive,READY,assets/sealed/hero.png
```

```text
python scripts/seal_evidence.py "<project>"
```

This creates a separate PNG, validates bounds, preserves RGBA and verifies source
regions after every overlay. Exact masks must be matching binary masks; no resizing
or feathering of evidence pixels is silently applied. Apply artistic feathering to
the surrounding free layer. Overlapping contradictory locks fail. The receipt links
raw generated base, source/mask hashes and the sealed candidate. Ingest the sealed
candidate; never overwrite an already ingested/reviewed candidate.

The retained `apply_locked_overlays.py` name forwards to this non-destructive path.

## Motion and actual trim evidence

`render_deterministic_shots.py` renders source HOLD/PUSH_IN/PULL_OUT/PAN/FADE shots.
It validates encoding, skips only matching previously verified renders, and requires
a versioned destination for changed outputs. Cropping must respect the approved frame
contract; a geometric crop can remove evidence even though it invents no pixels.

For a retrieved Flow clip:

```text
python scripts/extract_review_frames.py "<project>" "generated/flow_candidates/U1/<token>.mp4" --times "0,0.4,1,2,2.36,3.96"
python scripts/auto_qc_media.py "<project>"
```

Choose valid timestamps from the real duration/fps, especially intended cut times.
Register source/code-only frames with `register_asset.py` after agent review. Source
files use SOURCE_VERIFIED only after actual record-level historical verification.

## Assemble and finish

```text
python scripts/compile_direct_assembly.py "<project>"
python scripts/assemble_direct.py "<project>" --execute
```

The assembler refuses held units rather than dropping them, validates each trim and
full-decodes the picture master. Default output is `exports/direct_picture_master.mp4`.
To revise use a new `--output` version. Confirm actual joins and temp sound for G4.

After recording G4 for that exact picture file:

```text
python scripts/compile_ass_subtitles.py "<project>"
python scripts/mix_final_master.py "<project>" --execute
```

The sound plan is authoritative: missing listed audio is an error. Short narration is
padded to picture duration, preventing silent truncation of the picture. If no external
tracks are listed, preserve any picture audio. ASS is staged to a safe relative path
for FFmpeg on Windows. Default new typography is SimSun for Chinese and Times New Roman
for Latin/numbers; preserve an explicit approved design instead when supplied.

The `.qc.json` beside a rendered master records media decode/duration; it does not
claim an editorial review. `qc_project.py` is a retained broader planning audit; its
old profile/animatic labels are not additional human gates. Use it for relevant
evidence/coverage issues and document legacy-only warnings rather than forcing old
generated artifacts into a source-only production.

Final files remain drafts until the actual picture, text, audio, credits/disclosure
and requested deliverables are checked. Do not publish, send or upload a film merely
because local export passed; do so only within the user's requested delivery scope.
